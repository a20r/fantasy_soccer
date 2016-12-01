
import pandas as pd
import tabulate


PLAYERS_URL = "https://fantasy.premierleague.com/drf/elements/"


class Lineup(object):

    def __init__(self, starting, bench, cap, vice_cap):
        self.starting = starting
        self.bench = bench
        self.cap = cap
        self.vice_cap = vice_cap
        self.players = None

    def connect(self, players=None):
        if players:
            self.players = players
        else:
            self.players = pd.read_json(PLAYERS_URL)

    def get_name(self, player_id):
        p = self.get_player(player_id)
        return p["first_name"] + " " + p["second_name"]

    def get_player(self, player_id):
        if self.players is None:
            raise AttributeError("Lineup is not connected to a player DB")
        return self.players.query("'code' == {}".format(player_id))

    def __str__(self):
        pos = ["GK", "DEF", "MID", "FOR"]
        s_names, b_names = list(), list()
        s_pos, b_pos = list(), list()

        cap_name = self.get_name(self.cap)
        vice_cap_name = self.get_name(self.vice_cap)

        for i in self.starting:
            p = self.get_player(i)
            name = self.get_name(p)
            if name == cap_name:
                name += " (C)"
            if name == vice_cap_name:
                name += " (VC)"
            s_names.append(name)
            s_pos.append(pos[p["element_type"] - 1])

        for i in self.bench:
            p = self.get_player(i)
            b_names.append(p["first_name"] + " " + p["second_name"])
            b_pos.append(pos[p["element_type"] - 1])

        kwargs = dict(headers=["Name", "Position"], tablefmt="fancy_grid")
        s_tab = tabulate.tabulate(zip(s_names, s_pos), **kwargs)
        b_tab = tabulate.tabulate(zip(b_names, b_pos), **kwargs)
        print "Starting 11"
        print s_tab
        print "\nBench"
        print b_tab
