#!/usr/bin/env python3

import tweepy
import json
import http.server
import socketserver
from flask import Flask, render_template, redirect, request

class Timeline_List_Manager:
    def __init__(self):
        self.j = json.load(open("keys.json", mode="r"))
        self.main_account = "＊＊＊認証するアカウントのIDを入力＊＊＊"
        self.list_id = "＊＊＊TLリストのIDを入力＊＊＊"
        self.set_auth(self.main_account)

    def set_auth(self, userid):
        ACCESS_TOKEN = self.j["accounts"][userid]["ACCESS_TOKEN"]
        ACCESS_SECRET = self.j["accounts"][userid]["ACCESS_SECRET"]
        CONSUMER_KEY = self.j["via"]["CONSUMER_KEY"]
        CONSUMER_SECRET = self.j["via"]["CONSUMER_SECRET"]
        auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
        self.api = tweepy.API(auth)
        self.userid = userid

    # フォローユーザの取得
    def get_follow_users(self):
        follow_user_cursor = [friend_id for friend_id in tweepy.Cursor(self.api.friends_ids, user_id=self.api.me().id).items()]
        follow_user_list = self.api.lookup_users(user_ids=follow_user_cursor)
        return follow_user_list

    # フォロワーの取得
    def get_follower_users(self):
        follow_user_cursor = [friend_id for friend_id in tweepy.Cursor(self.api.followers_ids, user_id=self.api.me().id).items()]
        follow_user_list = self.api.lookup_users(user_ids=follow_user_cursor)
        return follow_user_list

    # リストユーザの取得
    def get_list_users(self, list_id):
        return tweepy.Cursor(self.api.list_members, list_id=list_id).items()

    # リストに追加されていないユーザの取得
    def get_new_follow_users(self, list_id):
        add_user_list = []
        list_id_list = self.list_to_id(self.get_list_users(list_id))
        for add_user in self.get_follow_users():
            exist = False
            for list_userid in list_id_list:
                if (add_user.screen_name == list_userid):
                    exist = True
                    break
            if not exist:
                add_user_list.append(add_user)

        return add_user_list

    # IDからリスト名を取得
    def get_list_name(self, list_id):
        list_obj = self.api.get_list(list_id=list_id)
        return list_obj.name

    # userオブジェクトのリストからtable内に記載するデータリストを生成
    def list_to_table(self, user_list):
        table_data_list = []
        for user in user_list:
            url = "https://twitter.com/" + user.screen_name
            table_data = Table_data(url, user.profile_image_url_https, user.name, user.screen_name)
            table_data_list.append(table_data)
        return table_data_list

    # userオブジェクトのリストからIDを抽出
    def list_to_id(self, user_list):
        ids = []
        for user in user_list:
            ids.append(user.screen_name)
        return ids

    # Webサーバ
    def server(self):
        app = Flask(__name__)
        a = [A_data("/follow", "フォロー"),
             A_data("/follower", "フォロワー"),
             A_data("/list?id=" + self.list_id, "TLリスト"),
             A_data("/new_follow?id=" + self.list_id, "新規フォロー")]

        @app.route("/")
        def index():
            table = self.list_to_table([self.api.me()])
            return render_template("index.html", title="TLリスト管理ツール", table=table, a=a)

        @app.route("/follow", methods=["get"])
        def find_follow_users():
            title = "フォロー一覧"
            table = self.list_to_table(self.get_follow_users())
            return render_template("table.html", title=title, a=a, table=table)

        @app.route("/follower", methods=["get"])
        def find_follower_users():
            title = "フォロワー一覧"
            table = self.list_to_table(self.get_follower_users())
            return render_template("table.html", title=title, a=a, table=table)

        @app.route("/list", methods=["get"])
        def find_tl_list_users():
            list_id = request.args.get("id")
            list_name = self.get_list_name(list_id)
            title = list_name + "一覧"
            table = self.list_to_table(self.get_list_users(list_id))
            btn = Btn_data("/remove_list_user", "解除", list_id)
            return render_template("table.html", title=title, table=table, a=a, list_id=list_id, btn=btn)

        @app.route("/new_follow", methods=["get"])
        def find_new_follow_users():
            list_id = request.args.get("id")
            list_name = self.get_list_name(list_id)
            title = list_name + "に未追加のフォローユーザ一覧"
            table = self.list_to_table(self.get_new_follow_users(list_id))
            btn = Btn_data("/add_list_user", "追加", list_id)
            return render_template("table.html", title=title, table=table, a=a, list_id=list_id, btn=btn)

        @app.route("/add_list_user", methods=["post"])
        def add_list_user():
            user_id = request.form.get("user_id")
            list_id = request.form.get("list_id")
            self.api.add_list_member(list_id=list_id, id=user_id)
            return redirect("/new_follow?id=" + list_id)

        @app.route("/remove_list_user", methods=["post"])
        def remove_list_user():
            user_id = request.form.get("user_id")
            list_id = request.form.get("list_id")
            self.api.remove_list_member(list_id=list_id, id=user_id)
            return redirect("/list?id=" + list_id)

        app.run(debug=True, port=8888, host="0.0.0.0", threaded=True)


class Table_data:
    def __init__(self, url, icon, name, user_id):
        self.url = url
        self.icon = icon
        self.name = name
        self.user_id = user_id

class A_data:
    def __init__(self, url, sentence):
        self.url = url
        self.sentence = sentence

class Btn_data:
    def __init__(self, url, sentence, list_id=""):
        self.url = url
        self.sentence = sentence
        self.list_id = list_id


if __name__ == "__main__":
    manager = Timeline_List_Manager()
    manager.server()
