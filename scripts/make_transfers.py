
import lineup
import pick_team
from gurobipy import Model, quicksum, GRB, tuplelist


def print_transfers(coming, leaving):
    print "Players in: " + "None" if len(coming) == 0 else ""
    for p in coming:
        print p

    print "Players out: " + "None" if len(leaving) == 0 else ""
    for p in leaving:
        print p


def construct_new_team(cur_lu, cur_xs, new_xs):
    best_team, prices = [], {}
    coming, leaving = [], []
    for x, p in new_xs:
        if x.x > 0.1:
            best_team.append(p["code"])
            prices.append(p["now_cost"])
            coming.append(cur_lu.get_name(p["code"]))

    for x, p in cur_xs:
        pcode = p["code"]
        if x.x > 0.1:
            best_team.append(pcode)
            prices[pcode] = cur_lu.get_org_cost(pcode)
        else:
            leaving.append(cur_lu.get_name(pcode))

    return best_team, prices, coming, leaving


def compute_money_diff(cur_lu, cur_xs, new_xs):
    money_in = list()
    for x, p in cur_xs:
        money_in.append((1 - x) * cur_lu.get_selling_price(p["code"]))

    money_out = list()
    for x, p in new_xs:
        money_out.append(x * p["now_cost"])
    return money_in, money_out


def make_transfers(players):
    m = Model("make_transfers")
    m.params.OutputFlag = 0
    cur_lu = lineup.Lineup().connect(players)
    new_xs, cur_xs = [], []
    team_pos = tuplelist()
    teams = [[] for _ in xrange(players.shape[0])]
    gks, defs, mids, fors = [], [], [], []
    assigns = [gks, defs, mids, fors]
    tcodes = set()

    for i in xrange(players.shape[0]):
        obj = pick_team.player_objective(players.iloc[i], 75)
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

    money_in, money_out = compute_money_diff(cur_lu, cur_xs, new_xs)

    pick_team.per_pos_team_constr(m, tcodes, team_pos)
    pick_team.total_team_constr(m, teams)

    m.addConstr(quicksum(gks) == 2)
    m.addConstr(quicksum(defs) == 5)
    m.addConstr(quicksum(mids) == 5)
    m.addConstr(quicksum(fors) == 3)
    m.addConstr(quicksum(money_out) <= quicksum(money_in))

    m.optimize()
    return construct_new_team(cur_lu, cur_xs, new_xs)


if __name__ == "__main__":
    players = pick_team.load_players()
    best_team, prices, coming, leaving = make_transfers(players)
    lu = pick_team.construct_lineup(players, best_team, prices)
    print_transfers(coming, leaving)
    print "\n", lu
