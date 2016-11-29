
import pandas as pd
from gurobipy import Model, quicksum, GRB


def pick_team():
    players = pd.read_json("https://fantasy.premierleague.com/drf/elements/")
    m = Model("pick_team")
    m.params.OutputFlag = 0
    xs = list()
    gks = list()
    defs = list()
    mids = list()
    fors = list()
    assigns = [gks, defs, mids, fors]
    teams = [[] for _ in xrange(players.shape[0])]

    for i in xrange(players.shape[0]):
        obj = 0
        chance_of_playing = players.iloc[i]["chance_of_playing_next_round"]
        if chance_of_playing >= 75:
            ppg = players.iloc[i]["points_per_game"]
            form = players.iloc[i]["form"]
            obj = -ppg * form
        ptype = players.iloc[i]["element_type"]
        tcode = players.iloc[i]["team_code"]
        v = m.addVar(vtype=GRB.BINARY, obj=obj)
        assigns[ptype - 1].append(v)
        teams[tcode - 1].append(v)
        xs.append(v)

    m.update()

    costs = list()
    for i in xrange(players.shape[0]):
        pcost = players.iloc[i]["now_cost"]
        costs.append(xs[i] * pcost)

    m.addConstr(quicksum(costs) <= 1000)
    m.addConstr(quicksum(xs) == 15)
    m.addConstr(quicksum(gks) == 2)
    m.addConstr(quicksum(defs) == 5)
    m.addConstr(quicksum(mids) == 5)
    m.addConstr(quicksum(fors) == 3)

    for team in teams:
        m.addConstr(quicksum(team) <= 3)

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
    gks = list()
    defs = list()
    mids = list()
    fors = list()
    assigns = [gks, defs, mids, fors]

    for player in team:
        obj = 0
        if player["chance_of_playing_next_round"] > 75:
            obj = -player["points_per_game"] * player["form"]
        ptype = player["element_type"]
        v = m.addVar(vtype=GRB.BINARY, obj=obj)
        assigns[ptype - 1].append(v)
        xs.append(v)

    m.update()

    m.addConstr(quicksum(xs) == 11)
    m.addConstr(quicksum(gks) == 1)
    m.addConstr(quicksum(defs) == 4)
    m.addConstr(quicksum(mids) == 4)
    m.addConstr(quicksum(fors) == 2)

    m.optimize()

    starting = list()
    bench = list()

    for i, v in enumerate(xs):
        if v.x > 0.1:
            starting.append(team[i])
        else:
            bench.append(team[i])

    return starting, bench


def print_lineup(starting, bench):
    print "Starting 11"
    print "======================"
    for p in starting:
        print p["first_name"], \
            p["second_name"], "|", \
            p["element_type"]

    print "\nBench"
    print "======================"
    for p in bench:
        print p["first_name"], \
            p["second_name"], "|", \
            p["element_type"]


if __name__ == "__main__":
    best_team = pick_team()
    starting, bench = select_players(best_team)
    print_lineup(starting, bench)
