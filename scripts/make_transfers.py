
import lineup
from pick_team import player_objective
from gurobipy import Model, quicksum, GRB


def make_transfers(players):
    m = Model("make_transfers")
    cur_lu = lineup.Lineup().connect(players)
    new_xs, cur_xs = [], []
    for i in xrange(players.shape[0]):
        obj = player_objective(players.iloc[i])
        v = m.addVar(vtype=GRB.BINARY, obj=obj)
        if players.iloc[i]["code"] in cur_lu:
            cur_xs.append((v, players.iloc[i]))
        else:
            new_xs.append((v, players.iloc[i]))

    m.update()

    money_in = list()
    for x, p in xrange(cur_xs):
        money_in.append(x * p["now_cost"])

    money_out = list()
    for x, p in xrange(new_xs):
        money_out.append(x * p["now_cost"])

    m.addConstr(quicksum(money_out) <= quicksum(money_in))
