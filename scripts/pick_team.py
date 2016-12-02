
import pandas as pd
import lineup
from gurobipy import Model, quicksum, GRB, tuplelist


PLAYERS_URL = "https://fantasy.premierleague.com/drf/elements/"


def load_players():
    players = pd.read_json(PLAYERS_URL)
    return players.set_index("code", drop=False)


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


def pick_team(players):
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
    prices = dict()
    for i, v in enumerate(xs):
        if v.x > 0.1:
            pcode = players.iloc[i]["code"]
            best_team.append(pcode)
            prices[pcode] = players.iloc[i]["now_cost"]

    return best_team, prices


def select_players(players, team):
    m = Model("select_players")
    m.params.OutputFlag = 0
    xs = list()
    gks, defs, mids, fors = [], [], [], []
    assigns = [gks, defs, mids, fors]

    for i in team:
        obj = player_objective(players.loc[i], 100)
        ptype = players.loc[i]["element_type"]
        v = m.addVar(vtype=GRB.BINARY, obj=obj)
        assigns[ptype - 1].append(v)
        xs.append(v)

    m.update()

    m.addConstr(quicksum(xs) == 11)
    m.addConstr(quicksum(gks) == 1)
    m.addConstr(quicksum(defs) >= 3)
    m.addConstr(quicksum(fors) >= 1)

    m.optimize()

    starting = list()
    bench = list()

    for i, v in enumerate(xs):
        if v.x > 0.1:
            starting.append(team[i])
        else:
            bench.append(team[i])

    key = lambda p: players.loc[p]["element_type"]
    starting = sorted(starting, key=key)
    bench = sorted(bench, key=key)

    return starting, bench


def select_captains(players, starting):
    key = lambda p: players.loc[p]["points_per_game"] * players.loc[p]["form"]
    starting_sorted = sorted(starting, key=key)
    captain = starting_sorted[-1]
    vice_captain = starting_sorted[-2]
    return captain, vice_captain


def construct_lineup(players, team, prices):
    starting, bench = select_players(players, team)
    cp, vcp = select_captains(players, starting)
    lu = lineup.Lineup(starting, bench, cp, vcp, prices)
    lu.connect(players)
    lu.write()
    return lu


if __name__ == "__main__":
    players = load_players()
    best_team, prices = pick_team(players)
    lu = construct_lineup(players, best_team, prices)
    print lu
