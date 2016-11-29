
import pandas as pd
import tabulate
from gurobipy import Model, quicksum, GRB, tuplelist


def per_pos_team_constr(m, tcodes, team_pos):
    for tc in tcodes:
        for i in xrange(1, 5):
            ps = list(team_pos.select("*", i, tc))
            m.addConstr(quicksum([p[0] for p in ps]) <= 2)


def total_team_constr(m, teams):
    for team in teams:
        m.addConstr(quicksum(team) <= 3)


def total_cost_constr(m, xs, players):
    costs = list()
    for i in xrange(players.shape[0]):
        pcost = players.iloc[i]["now_cost"]
        costs.append(xs[i] * pcost)
    m.addConstr(quicksum(costs) <= 1000)


def player_objective(player, thresh):
    obj = 0
    chance_of_playing = player["chance_of_playing_next_round"]
    if chance_of_playing >= thresh:
        ppg = player["points_per_game"]
        form = player["form"]
        obj = -ppg * form
    return obj


def pick_team():
    players = pd.read_json("https://fantasy.premierleague.com/drf/elements/")
    m = Model("pick_team")
    m.params.OutputFlag = 0
    xs = list()
    gks, defs, mids, fors = [], [], [], []
    assigns = [gks, defs, mids, fors]
    teams = [[] for _ in xrange(players.shape[0])]
    team_pos = tuplelist()
    tcodes = set()

    for i in xrange(players.shape[0]):
        obj = player_objective(players.iloc[i], 75)
        ptype = players.iloc[i]["element_type"]
        tcode = players.iloc[i]["team_code"]
        v = m.addVar(vtype=GRB.BINARY, obj=obj)
        assigns[ptype - 1].append(v)
        teams[tcode - 1].append(v)
        team_pos.append((v, ptype, tcode))
        tcodes.add(tcode)
        xs.append(v)

    m.update()

    per_pos_team_constr(m, tcodes, team_pos)
    total_cost_constr(m, xs, players)
    total_team_constr(m, teams)

    m.addConstr(quicksum(xs) == 15)
    m.addConstr(quicksum(gks) == 2)
    m.addConstr(quicksum(defs) == 5)
    m.addConstr(quicksum(mids) == 5)
    m.addConstr(quicksum(fors) == 3)

    m.optimize()

    best_team = list()
    for i, v in enumerate(xs):
        if v.x > 0.1:
            best_team.append(players.iloc[i])

    return best_team


def select_players(team):
    m = Model("select_players")
    m.params.OutputFlag = 0
    xs = list()
    gks, defs, mids, fors = [], [], [], []
    assigns = [gks, defs, mids, fors]

    for player in team:
        obj = player_objective(player, 100)
        ptype = player["element_type"]
        v = m.addVar(vtype=GRB.BINARY, obj=obj)
        assigns[ptype - 1].append(v)
        xs.append(v)

    m.update()

    m.addConstr(quicksum(xs) == 11)
    m.addConstr(quicksum(gks) == 1)
    m.addConstr(quicksum(defs) >= 3)
    # m.addConstr(quicksum(mids) == 4)
    m.addConstr(quicksum(fors) >= 1)

    m.optimize()

    starting = list()
    bench = list()

    for i, v in enumerate(xs):
        if v.x > 0.1:
            starting.append(team[i])
        else:
            bench.append(team[i])

    key = lambda p: p["element_type"]
    starting = sorted(starting, key=key)
    bench = sorted(bench, key=key)

    return starting, bench


def select_captains(starting):
    key = lambda p: p["points_per_game"] * p["form"]
    starting_sorted = sorted(starting, key=key)
    captain = starting_sorted[-1]
    vice_captain = starting_sorted[-2]
    return captain, vice_captain


def get_name(player):
    return player["first_name"] + " " + player["second_name"]


def print_lineup(starting, bench, cap, vice_cap):
    pos = ["GK", "DEF", "MID", "FOR"]
    s_names, b_names = list(), list()
    s_pos, b_pos = list(), list()

    cap_name = get_name(cap)
    vice_cap_name = get_name(vice_cap)

    for p in starting:
        name = get_name(p)
        if name == cap_name:
            name += " (C)"
        if name == vice_cap_name:
            name += " (VC)"
        s_names.append(name)
        s_pos.append(pos[p["element_type"] - 1])

    for p in bench:
        b_names.append(p["first_name"] + " " + p["second_name"])
        b_pos.append(pos[p["element_type"] - 1])

    kwargs = dict(headers=["Name", "Position"], tablefmt="fancy_grid")
    s_tab = tabulate.tabulate(zip(s_names, s_pos), **kwargs)
    b_tab = tabulate.tabulate(zip(b_names, b_pos), **kwargs)
    print "Starting 11"
    print s_tab
    print "\nBench"
    print b_tab


if __name__ == "__main__":
    best_team = pick_team()
    starting, bench = select_players(best_team)
    cp, vcp = select_captains(starting)
    print_lineup(starting, bench, cp, vcp)
