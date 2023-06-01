#!/usr/bin/env python3.10

"""A simple Multi-User Dungeon (MUD) game. Players can talk to each
other, examine their surroundings and move between rooms.

Some ideas for things to try adding:
    * More rooms to explore
    * An 'emote' command e.g. 'emote laughs out loud' -> 'Mark laughs
        out loud'
    * A 'whisper' command for talking to individual players
    * A 'shout' command for yelling to players in all rooms
    * Items to look at in rooms e.g. 'look fireplace' -> 'You see a
        roaring, glowing fire'
    * Items to pick up e.g. 'take rock' -> 'You pick up the rock'
    * Monsters to fight
    * Loot to collect
    * Saving players accounts between sessions
    * A password login
    * A shop from which to buy items

author: Mark Frimston - mfrimston@gmail.com
"""

import time
import mysql.connector
import json

# import the MUD server class
from mudserver import MudServer


def delinventory(pid, itemid):
    with open('db.json', 'r') as openfile:
        json_object = json.load(openfile)

    mydb = mysql.connector.connect(
        host=json_object['host'],
        user=json_object['username'],
        password=json_object['password'],
        database=json_object['database']
    )
    mycursor = mydb.cursor()
    mycursor.execute("DELETE FROM inventory WHERE itemid = %s AND playerid = %s LIMIT 1", (itemid, pid))
    mydb.commit()


def addinventory(pid, itemid):
    with open('db.json', 'r') as openfile:
        json_object = json.load(openfile)

    mydb = mysql.connector.connect(
        host=json_object['host'],
        user=json_object['username'],
        password=json_object['password'],
        database=json_object['database']
    )
    mycursor = mydb.cursor()
    mycursor.execute("INSERT INTO inventory (itemid, playerid) VALUES(%s, %s)", (itemid, pid))
    mydb.commit()


def loadplayer(player):
    with open('db.json', 'r') as openfile:
        json_object = json.load(openfile)

    mydb = mysql.connector.connect(
        host=json_object['host'],
        user=json_object['username'],
        password=json_object['password'],
        database=json_object['database']
    )
    mycursor = mydb.cursor()
    mycursor.execute("SELECT id, name, password, lastroom FROM players WHERE name = %s AND password = %s",
                     (player['name'], player['password']))
    row = mycursor.fetchone()
    if row is None:
        return False
    else:
        player['dbid'] = row[0]
        player['room'] = row[3]
        mycursor.execute("SELECT itemid FROM inventory WHERE playerid = %s", (row[0],))
        res = mycursor.fetchall()
        for irow in res:
            player['inventory'].append(loaditem(irow[0]))

        return True


def checkname(name):
    with open('db.json', 'r') as openfile:
        json_object = json.load(openfile)

    mydb = mysql.connector.connect(
        host=json_object['host'],
        user=json_object['username'],
        password=json_object['password'],
        database=json_object['database']
    )
    mycursor = mydb.cursor()
    mycursor.execute("SELECT name FROM players WHERE name = %s", (name,))
    row = mycursor.fetchone()
    if row is None:
        return True
    else:
        return False


def updateplayerroom(player):
    with open('db.json', 'r') as openfile:
        json_object = json.load(openfile)

    mydb = mysql.connector.connect(
        host=json_object['host'],
        user=json_object['username'],
        password=json_object['password'],
        database=json_object['database']
    )
    mycursor = mydb.cursor()
    mycursor.execute("UPDATE players SET lastroom=%s WHERE name = %s", (player['room'], player['name']))
    mydb.commit()


def instplayer(player):
    with open('db.json', 'r') as openfile:
        json_object = json.load(openfile)

    mydb = mysql.connector.connect(
        host=json_object['host'],
        user=json_object['username'],
        password=json_object['password'],
        database=json_object['database']
    )
    mycursor = mydb.cursor()
    mycursor.execute("INSERT INTO players (name, password, lastroom) VALUES(%s, %s, 1)",
                     (player['name'], player['password']))
    mydb.commit()
    player['dbid'] = mycursor.lastrowid


def loaditem(itemid):
    with open('db.json', 'r') as openfile:
        json_object = json.load(openfile)

    mydb = mysql.connector.connect(
        host=json_object['host'],
        user=json_object['username'],
        password=json_object['password'],
        database=json_object['database']
    )
    mycursor = mydb.cursor()
    mycursor.execute("SELECT id, name, description, invulnerable, isuniq FROM itemdef WHERE id = %s", (itemid,))
    row = mycursor.fetchone()

    item = {'id': row[0], 'name': row[1], 'description': row[2], 'invulnerable': row[3], 'isuniq': row[4]}

    return item


def loaditems(room):
    with open('db.json', 'r') as openfile:
        json_object = json.load(openfile)

    mydb = mysql.connector.connect(
        host=json_object['host'],
        user=json_object['username'],
        password=json_object['password'],
        database=json_object['database']
    )
    mycursor = mydb.cursor()
    mycursor.execute("SELECT objid FROM roominv WHERE roomid = %s", (room['id'],))
    myresult = mycursor.fetchall()
    for row in myresult:
        mycursor.execute("SELECT name, description, movable, failtake, takesuccess, takeitem FROM objdef WHERE id = %s",
                         (row[0],))
        objrow = mycursor.fetchone()
        room['items'].append(
            {'id': row[0], 'name': objrow[0], 'description': objrow[1], 'movable': objrow[2], 'failtake': objrow[3],
             'takesuccess': objrow[4], 'takeitem': objrow[5]})


def findroom(id):
    for rm in rooms:
        if rm['id'] == id:
            return rm

    return rooms[0]


def loadrooms():
    with open('db.json', 'r') as openfile:
        json_object = json.load(openfile)

    mydb = mysql.connector.connect(
        host=json_object['host'],
        user=json_object['username'],
        password=json_object['password'],
        database=json_object['database']
    )

    mycursor = mydb.cursor()
    mycursor.execute("SELECT id, name, description FROM roomdef")
    myresult = mycursor.fetchall()

    rooms = []

    for row in myresult:
        room = {'id': row[0], 'name': row[1], 'description': row[2], 'exits': [], 'items': []}
        mycursor.execute("SELECT id, name, toroom FROM exitdef WHERE fromroom = %s", (row[0],))
        exresult = mycursor.fetchall()

        for exrow in exresult:
            room['exits'].append({'name': exrow[1], 'toroom': exrow[2]})

        rooms.append(room)

    return rooms


# stores the players in the game
players = {}

# start the server
mud = MudServer()

rooms = loadrooms()
for room in rooms:
    loaditems(room)

# main game loop. We loop forever (i.e. until the program is terminated)
while True:

    # pause for 1/5 of a second on each loop, so that we don't constantly
    # use 100% CPU time
    time.sleep(0.2)

    # 'update' must be called in the loop to keep the game running and give
    # us up-to-date information
    mud.update()

    # go through any newly connected players
    for id in mud.get_new_players():
        # add the new player to the dictionary, noting that they've not been
        # named yet.
        # The dictionary key is the player's id number. We set their room to
        # None initially until they have entered a name
        # Try adding more player stats - level, gold, inventory, etc
        players[id] = {
            "name": None,
            "room": None,
            "dbid": None,
            "password": None,
            "newplayer": False,
            "inventory": []
        }

        # send the new player a prompt for their name
        mud.send_message(id, "What is your name?")

    # go through any recently disconnected players
    for id in mud.get_disconnected_players():

        # if for any reason the player isn't in the player map, skip them and
        # move on to the next one
        if id not in players:
            continue

        # go through all the players in the game
        for pid, pl in players.items():
            # send each player a message to tell them about the diconnected
            # player
            mud.send_message(pid, "{} quit the game".format(
                players[id]["name"]))

        # remove the player's entry in the player dictionary
        del (players[id])

    # go through any new commands sent from players
    for id, command, params in mud.get_commands():

        # if for any reason the player isn't in the player map, skip them and
        # move on to the next one
        if id not in players:
            continue

        # if the player hasn't given their name yet, use this first command as
        # their name and move them to the starting room.
        if players[id]["name"] is None:

            if command.lower() == "new":
                players[id]["newplayer"] = True
                mud.send_message(id, "What would you like your name to be?")
            else:
                if players[id]["newplayer"]:
                    if checkname(command):
                        players[id]["name"] = command
                        mud.send_message(id, "Choose a password?")
                    else:
                        mud.send_message(id, "Sorry, that name is in use, try again.")
                else:
                    players[id]["name"] = command
                    mud.send_message(id, "What is your password? ")

        elif players[id]["password"] is None:
            players[id]["password"] = command

            shouldcontinue = False
            for pid, pl in players.items():
                if pid != id:
                    if players[pid]['name'] == players[id]['name']:
                        del (players[id])
                        mud.disconnect(id)
                        shouldcontinue = True
                        break
            if shouldcontinue:
                continue

            if not players[id]["newplayer"]:
                if not loadplayer(players[id]):
                    del (players[id])
                    mud.disconnect(id)
                    continue
            else:
                players[id]["room"] = 1
                instplayer(players[id])

            # go through all the players in the game
            for pid, pl in players.items():
                # send each player a message to tell them about the new player
                mud.send_message(pid, "{} entered the game".format(
                    players[id]["name"]))

            # send the new player a welcome message
            mud.send_message(id, "Welcome to the game, {}. ".format(
                players[id]["name"])
                             + "Type 'help' for a list of commands. Have fun!")

            # send the new player the description of their current room
            mud.send_message(id, findroom(players[id]["room"])["description"])

        # each of the possible commands is handled below. Try adding new
        # commands to the game!

        elif command == "quit":
            del (players[id])
            mud.disconnect(id)
            continue

        # 'help' command
        elif command == "help":

            # send the player back the list of possible commands
            mud.send_message(id, "Commands:")
            mud.send_message(id, "  say <message>  - Says something out loud, "
                             + "e.g. 'say Hello'")
            mud.send_message(id, "  look           - Examines the "
                             + "surroundings, e.g. 'look'")
            mud.send_message(id, "  examine <item> - Examines an "
                             + "item, e.g. 'examine fireplace'")
            mud.send_message(id, "  inventory      - Lists your inventory")
            mud.send_message(id, "  take <item>    - Take an "
                             + "item, e.g. 'take fireplace'")
            mud.send_message(id, "  drop <item>    - Destroy an inventory "
                             + "item")
            mud.send_message(id, "  go <exit>      - Moves through the exit "
                             + "specified, e.g. 'go outside'")
            mud.send_message(id, "  quit           - Disconnects from the game")

        # 'say' command
        elif command == "say":

            # go through every player in the game
            for pid, pl in players.items():
                # if they're in the same room as the player
                if players[pid]["room"] == players[id]["room"]:
                    # send them a message telling them what the player said
                    mud.send_message(pid, "{} says: {}".format(
                        players[id]["name"], params))

        elif command == "drop":
            ex = params.lower()
            found = False
            for it in players[id]['inventory']:
                if it['name'] == ex:
                    found = True
                    if not it['invulnerable']:
                        mud.send_message(id, "You dropped {} and it vanished in thin air!".format(it['name']))
                        delinventory(players[id]['dbid'], it['id'])
                        players[id]['inventory'].remove(it)
                    else:
                        mud.send_message(id, "You can't drop {}".format(it['name']))
                    break
            if not found:
                mud.send_message(id, "You have no {} to drop".format(ex))

        elif command == "take":
            rm = findroom(players[id]["room"])
            found = False
            ex = params.lower()

            for it in rm['items']:
                if it['name'] == ex:
                    if not it['movable']:
                        mud.send_message(id, it['failtake'])
                    else:
                        failtake = False
                        for uniq in players[id]['inventory']:
                            if uniq['id'] == it['takeitem'] and uniq['isuniq']:
                                failtake = True
                                break
                        if not failtake:
                            mud.send_message(id, it['takesuccess'])
                            players[id]['inventory'].append(loaditem(it['takeitem']))
                            addinventory(players[id]['dbid'], it['takeitem'])
                        else:
                            mud.send_message(id, it['failtake'])
                found = True
                break

            if not found:
                mud.send_message(id, "take what?!")

        elif command == "inventory":
            mud.send_message(id, "Your Inventory:")
            for item in players[id]['inventory']:
                mud.send_message(id, " - {}".format(item['name']))

        elif command == "examine":
            rm = findroom(players[id]["room"])
            found = False
            ex = params.lower()

            for it in rm['items']:
                if it['name'] == ex:
                    mud.send_message(id, it["description"])
                    found = True
                    break

            if not found:
                for it in players[id]['inventory']:
                    if it['name'] == ex:
                        mud.send_message(id, it['description'])
                        found = True
                        break

            if not found:
                mud.send_message(id, "examine what?!")

        elif command == "look":
            # store the player's current room
            rm = findroom(players[id]["room"])

            # send the player back the description of their current room
            mud.send_message(id, rm["description"])

            playershere = []
            # go through every player in the game
            for pid, pl in players.items():
                # if they're in the same room as the player
                if players[pid]["room"] == players[id]["room"]:
                    # ... and they have a name to be shown
                    if players[pid]["name"] is not None:
                        # add their name to the list
                        playershere.append(players[pid]["name"])

            # send player a message containing the list of players in the room
            mud.send_message(id, "Players here: {}".format(
                ", ".join(playershere)))

            # send player a message containing the list of exits from this room
            exitshere = []
            for ex in rm['exits']:
                exitshere.append(ex['name'])

            mud.send_message(id, "Exits are: {}".format(
                ", ".join(exitshere)))

            itemshere = []
            for it in rm['items']:
                itemshere.append(it['name'])

            mud.send_message(id, "Items are: {}".format(", ".join(itemshere)))

        # 'go' command
        elif command == "go":

            # store the exit name
            ex = params.lower()

            # store the player's current room
            rm = findroom(players[id]["room"])
            found = False
            # if the specified exit is found in the room's exits list
            for rex in rm["exits"]:
                if rex["name"] == ex:
                    # go through all the players in the game
                    for pid, pl in players.items():
                        # if player is in the same room and isn't the player
                        # sending the command
                        if players[pid]["room"] == players[id]["room"] \
                                and pid != id:
                            # send them a message telling them that the player
                            # left the room
                            mud.send_message(pid, "{} left via exit '{}'".format(
                                players[id]["name"], rex["name"]))

                    # update the player's current room to the one the exit leads to
                    players[id]["room"] = rex['toroom']
                    rm = findroom(players[id]["room"])

                    # go through all the players in the game
                    for pid, pl in players.items():
                        # if player is in the same (new) room and isn't the player
                        # sending the command
                        if players[pid]["room"] == players[id]["room"] \
                                and pid != id:
                            # send them a message telling them that the player
                            # entered the room
                            mud.send_message(pid,
                                             "{} arrived via exit '{}'".format(
                                                 players[id]["name"], rex["name"]))

                    # send the player a message telling them where they are now
                    mud.send_message(id, "You arrive at '{}'".format(
                        findroom(players[id]["room"])["name"]))
                    found = True
                    updateplayerroom(players[id])
                # the specified exit wasn't found in the current room
            if not found:
                # send back an 'unknown exit' message
                mud.send_message(id, "Unknown exit '{}'".format(ex))

        # some other, unrecognised command
        else:
            # send back an 'unknown command' message
            mud.send_message(id, "Unknown command '{}'".format(command))
