
import lineup
from pick_team import player_objective, per_pos_team_constr, total_team_constr
from pick_team import load_players
from gurobipy import Model, quicksum, GRB, tuplelist


def make_transfers(players):
    m = Model("make_transfers")
    cur_lu = lineup.Lineup().connect(players)
    new_xs, cur_xs = [], []
    team_pos = tuplelist()
    teams = [[] for _ in xrange(players.shape[0])]
    gks, defs, mids, fors = [], [], [], []
    assigns = [gks, defs, mids, fors]
    tcodes = set()

    for i in xrange(players.shape[0]):
        obj = player_objective(players.iloc[i], 75)
        v = m.addVar(vtype=GRB.BINARY, obj=obj)
        if players.iloc[i]["code"] in cur_lu:
            cur_xs.append((v, players.iloc[i]))
        else:
            new_xs.append((v, players.iloc[i]))
        ptype = players.iloc[i]["element_type"]
        tcode = players.iloc[i]["team_code"]
        assigns[ptype - 1].append(v)
        teams[tcode - 1].append(v)
        tcodes.add(tcode)
        team_pos.append((v, ptype, tcode))

    m.update()

    per_pos_team_constr(m, tcodes, team_pos)
    total_team_constr(m, teams)

    m.addConstr(quicksum(gks) == 2)
    m.addConstr(quicksum(defs) == 5)
    m.addConstr(quicksum(mids) == 5)
    m.addConstr(quicksum(fors) == 3)

    money_in = list()
    for x, p in cur_xs:
        money_in.append((1 - x) * p["now_cost"])

    money_out = list()
    for x, p in new_xs:
        money_out.append(x * p["now_cost"])

    m.addConstr(quicksum(money_out) <= quicksum(money_in))

    m.optimize()

    print "Players in:"
    for x, p in new_xs:
        if x.x > 0.1:
            print p["web_name"]

    print "Players out:"
    for x, p in cur_xs:
        if x.x < 0.1:
            print p["web_name"]


if __name__ == "__main__":
    players = load_players()
    make_transfers(players)
