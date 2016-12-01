
import pandas as pd
import tabulate
import json
import datetime


PLAYERS_URL = "https://fantasy.premierleague.com/drf/elements/"


class Lineup(object):

    def __init__(self, starting=None, bench=None, cap=None, vice_cap=None):
        if starting is None:
            starting = "lineups/latest.json"
        if type(starting) == list:
            self.starting = starting
            self.bench = bench
            self.cap = cap
            self.vice_cap = vice_cap
            self.players = None
        elif type(starting) == str:
            with open(starting) as f:
                lu_dict = json.loads(f.read())
                self.starting = lu_dict["starting"]
                self.bench = lu_dict["bench"]
                self.cap = lu_dict["captain"]
                self.vice_cap = lu_dict["vice_captain"]

    def connect(self, players=None):
        if players is None:
            self.players = pd.read_json(PLAYERS_URL)
        else:
            self.players = players
        return self

    def get_name(self, player_id):
        p = self.get_player(player_id)
        return p["first_name"] + " " + p["second_name"]

    def get_player(self, player_id):
        if self.players is None:
            raise AttributeError("Lineup is not connected to a player DB")
        return self.players.loc[player_id]

    def to_dict(self):
        lineup_dict = dict()
        lineup_dict["starting"] = self.starting
        lineup_dict["bench"] = self.bench
        lineup_dict["captain"] = self.cap
        lineup_dict["vice_captain"] = self.vice_cap
        return lineup_dict

    def write(self):
        lu_dict = self.to_dict()
        j_str = json.dumps(lu_dict)
        now = datetime.datetime.now()
        now_f = "lineups/{}.json".format(now.strftime("%d-%m-%y-%H-%M-%S"))
        lat_f = "lineups/latest.json"
        with open(now_f, "w") as f_now, open(lat_f, "w") as f_lat:
            f_now.write(j_str)
            f_lat.write(j_str)

    def __str__(self):
        pos = ["GK", "DEF", "MID", "FOR"]
        s_names, b_names = list(), list()
        s_pos, b_pos = list(), list()

        cap_name = self.get_name(self.cap)
        vice_cap_name = self.get_name(self.vice_cap)

        for i in self.starting:
            name = self.get_name(i)
            if name == cap_name:
                name += " (C)"
            if name == vice_cap_name:
                name += " (VC)"
            s_names.append(name)
            s_pos.append(pos[self.players.loc[i]["element_type"] - 1])

        for i in self.bench:
            p = self.get_player(i)
            b_names.append(p["first_name"] + " " + p["second_name"])
            b_pos.append(pos[p["element_type"] - 1])

        kwargs = dict(headers=["Name", "Position"], tablefmt="fancy_grid")
        s_tab = tabulate.tabulate(zip(s_names, s_pos), **kwargs)
        b_tab = tabulate.tabulate(zip(b_names, b_pos), **kwargs)
        ret_str = unicode()
        ret_str += "Starting 11\n"
        ret_str += s_tab
        ret_str += "\n\nBench\n"
        ret_str += b_tab
        return ret_str.encode("utf-8", "ignore")

    def __contains__(self, item):
        return item in self.starting or item in self.bench
