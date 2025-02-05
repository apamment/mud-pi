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
import bcrypt

# import the MUD server class
from mudserver import MudServer


def putattrib(pid, attrib, value):
    with open('db.json', 'r') as openfile:
        json_object = json.load(openfile)

    mydb = mysql.connector.connect(
        host=json_object['host'],
        user=json_object['username'],
        password=json_object['password'],
        database=json_object['database']
    )
    mycursor = mydb.cursor()
    mycursor.execute("SELECT id FROM playerattr WHERE pid = %s AND attrib = %s", (pid, attrib))
    row = mycursor.fetchone()
    if row is None:
        mycursor.execute("INSERT INTO playerattr (pid, attrib, value) VALUES(%s, %s, %s)", (pid, attrib, value))
    else:
        mycursor.execute("UPDATE playerattr SET value = %s WHERE id = %s", (value, row[0]))
    mydb.commit()


def getattrib(pid, attrib, defvalue):
    with open('db.json', 'r') as openfile:
        json_object = json.load(openfile)

    mydb = mysql.connector.connect(
        host=json_object['host'],
        user=json_object['username'],
        password=json_object['password'],
        database=json_object['database']
    )
    mycursor = mydb.cursor()
    mycursor.execute("SELECT value FROM playerattr WHERE pid = %s AND attrib = %s", (pid, attrib))
    row = mycursor.fetchone()
    if row is None:
        return defvalue
    else:
        return row[0]


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
    mycursor.execute("SELECT id, name, password, lastroom FROM players WHERE name = %s",
                     (player['name'], ))
    row = mycursor.fetchone()
    if row is None:
        return False
    else:
        if bcrypt.checkpw(player['password'].encode('utf-8'), row[2].encode('utf-8')):
            player['dbid'] = row[0]
            player['room'] = row[3]
            mycursor.execute("SELECT itemid FROM inventory WHERE playerid = %s", (row[0],))
            res = mycursor.fetchall()
            for irow in res:
                player['inventory'].append(loaditem(irow[0]))

            return True
        return False


def checkname(name):
    if name.lower() == "new":
        return False
    elif not name.isalnum():
        return False
    elif len(name) < 2:
        return False
    else:
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
                     (player['name'], bcrypt.hashpw(player['password'].encode('utf-8'), bcrypt.gensalt())))
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
    mycursor.execute("SELECT id, name, description, invulnerable, isuniq, isarmor, isweapon, power, basevalue, bound "
                     "FROM itemdef WHERE id = %s", (itemid,))
    row = mycursor.fetchone()

    item = {'id': row[0], 'name': row[1], 'description': row[2].replace('\n', '\n\r'), 'invulnerable': row[3],
            'isuniq': row[4], 'isarmor': row[5], 'isweapon': row[6], 'power': row[7], 'basevalue': row[8],
            'bound': row[9]}

    return item


def str2bool(v):
    if v == "True":
        return True
    return False

def loadnpcs(room):
    with open('db.json', 'r') as openfile:
        json_object = json.load(openfile)

    mydb = mysql.connector.connect(
        host=json_object['host'],
        user=json_object['username'],
        password=json_object['password'],
        database=json_object['database']
    )
    mycursor = mydb.cursor()
    mycursor.execute("SELECT npcid FROM roomnpc WHERE roomid = %s", (room['id'],))
    myresult = mycursor.fetchall()
    for row in myresult:
        mycursor.execute("SELECT name, description, code, arg FROM npcdef WHERE id = %s",
                         (row[0],))
        npcrow = mycursor.fetchone()
        room['npcs'].append({'id': row[0], 'name': npcrow[0], 'description': npcrow[1].replace('\n', '\n\r'),
                             'code': npcrow[2], 'arg': npcrow[3]})


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
            {'id': row[0], 'name': objrow[0], 'description': objrow[1].replace('\n', '\n\r'), 'movable': objrow[2], 'failtake': objrow[3],
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
        room = {'id': row[0], 'name': row[1], 'description': row[2].replace('\n', '\n\r'), 'exits': [], 'items': [],
                'npcs': []}
        mycursor.execute("SELECT id, name, toroom, itemkey, failkey FROM exitdef WHERE fromroom = %s", (row[0],))
        exresult = mycursor.fetchall()

        for exrow in exresult:
            room['exits'].append({'name': exrow[1], 'toroom': exrow[2], 'itemkey': exrow[3], 'failkey': exrow[4]})

        rooms.append(room)

    return rooms


def cmd_look(id, rm):
    # send the player back the description of their current room
    mud.send_message(id, "\n\r%bold%cyan" + rm["name"] + "\r\n")
    mud.send_message(id, rm["description"] + "\r\n")

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
    mud.send_message(id, "%cyanPlayers: %reset{}".format(
        ", ".join(playershere)))

    # send player a message containing the list of exits from this room
    exitshere = []
    for ex in rm['exits']:
        exitshere.append(ex['name'])

    mud.send_message(id, "%cyanExits: %reset{}".format(
        ", ".join(exitshere)))

    itemshere = []
    for it in rm['items']:
        itemshere.append(it['name'])

    mud.send_message(id, "%cyanObjects: %reset{}".format(", ".join(itemshere)))

    npcshere = []
    for it in rm['npcs']:
        npcshere.append(it['name'])

    mud.send_message(id, "%cyanNPCs: %reset{}".format(", ".join(npcshere)))

# stores the players in the game
players = {}

# start the server
mud = MudServer()

rooms = loadrooms()
for room in rooms:
    loaditems(room)
    loadnpcs(room)

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
            "health": 100,
            "gold": 0,
            "color": True,
            "armor": None,
            "weapon": None,
            "target": None,
            "inventory": []
        }

        motdFile = open("motd.txt", "r")
        motdLines = motdFile.readlines()
        motdFile.close()
        linesCount = len(motdLines)
        for l in motdLines:
            mud.send_message(id, l[:-1], auth=False)

        # send the new player a prompt for their name
        mud.send_message(id, "What is your name? (or 'new' for a new player)", auth=False)

    # go through any recently disconnected players
    for id in mud.get_disconnected_players():

        # if for any reason the player isn't in the player map, skip them and
        # move on to the next one
        if id not in players:
            continue

        # go through all the players in the game
        for pid, pl in players.items():
            # send each player a message to tell them about the disconnected
            # player
            if pid != id and players[id]["password"]:
                mud.send_message(pid, "%bold%yellow{} quit the game".format(
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
                mud.send_message(id, "What would you like your name to be?", auth=False)
            else:
                if players[id]["newplayer"]:
                    if checkname(command):
                        players[id]["name"] = command
                        mud.send_message(id, "Choose a password?", auth=False)
                    else:
                        mud.send_message(id, "Sorry, that name is in use or inappropriate, try again.", 'red',
                                         auth=False)
                else:
                    players[id]["name"] = command
                    mud.send_message(id, "What is your password? ", auth=False)

        elif players[id]["password"] is None:
            if len(command) < 8 and players[id]["newplayer"]:
                mud.send_message(id, "Password too short!", 'red', auth=False)
                mud.send_message(id, "Choose a password?", auth=False)
                continue

            players[id]["password"] = command

            shouldcontinue = False
            for pid, pl in players.items():
                if pid != id:
                    if players[pid]['name'] == players[id]['name']:
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
                    players[id]["health"] = int(getattrib(players[id]["dbid"], "health", "100"))
                    players[id]["gold"] = int(getattrib(players[id]["dbid"], "gold", "0"))
                    players[id]["color"] = str2bool(getattrib(players[id]["dbid"], "color", "True"))
                    a = int(getattrib(players[id]["dbid"], "armor", "0"))
                    if a != 0:
                        players[id]["armor"] = loaditem(a)
                    w = int(getattrib(players[id]["dbid"], "weapon", "0"))
                    if w != 0:
                        players[id]["weapon"] = loaditem(w)

                    if not players[id]["color"]:
                        mud.togglecolor(id)
                    mud.authenticate(id)
            else:
                players[id]["room"] = 1
                players[id]["health"] = 100
                players[id]["gold"] = 0
                instplayer(players[id])
                mud.authenticate(id)

            # go through all the players in the game
            for pid, pl in players.items():
                # send each player a message to tell them about the new player
                mud.send_message(pid, "%bold%yellow{} entered the game".format(
                    players[id]["name"]))

            # send the new player a welcome message
            mud.send_message(id, "Welcome to the game, {}. ".format(
                players[id]["name"])
                             + "Type 'help' for a list of commands. Have fun!\r\n", 'magenta')

            # send the new player the description of their current room
            rm = findroom(players[id]["room"])

            cmd_look(id, rm)
            mud.send_message(id, "\n\r{} [%bold%yellow{} gold%reset] [%bold%red{} HP%reset] :> ".format(
                players[id]['name'], players[id]['gold'], players[id]['health']), lineend="")

        # each of the possible commands is handled below. Try adding new
        # commands to the game!
        elif players[id]['target'] is not None:
            # NPC CODE 1 = SCRAPBOT
            if players[id]['target']['code'] == 1:
                if command == "help":
                    mud.send_message(id, "I am a scrapbot, I turn unwanted items into gold!", lineend="\n\r\n\r")
                    mud.send_message(id, "I answer to the following commands:")
                    mud.send_message(id, "  appraise <item> - tell you how much <item> is worth.")
                    mud.send_message(id, "                    eg: 'appraise sword'")
                    mud.send_message(id, "  scrap <item>    - make the exchange. THIS CAN NOT BE UNDONE! ")
                    mud.send_message(id, "                    eg: 'scrap sword'")
                    mud.send_message(id, "  bye             - leave me in peace.")

                elif command == "appraise":
                    ex = params.lower()
                    found = False
                    for it in players[id]['inventory']:
                        if it['name'] == ex:
                            if it['basevalue'] > 0:
                                val = int(it['basevalue'] * 0.10)
                                mud.send_message(id, "That {} looks like it's worth {} gold".format(it['name'], val))
                            else:
                                mud.send_message(id, "That item has no value!")

                            found = True
                            break
                    if not found:
                        mud.send_message(id, "appraise what?")

                elif command == "scrap":
                    ex = params.lower()
                    found = False
                    for it in players[id]['inventory']:
                        if it['name'] == ex:
                            if it['basevalue'] > 0:
                                val = int(it['basevalue'] * 0.10)
                                players[id]['gold'] += val
                                delinventory(players[id]['dbid'], it['id'])
                                putattrib(players[id]['dbid'], "gold", str(players[id]['gold']))
                                mud.send_message(id, "Here's {} gold for your {}".format(val, it['name']))
                                players[id]['inventory'].remove(it)
                            else:
                                mud.send_message(id, "That item has no value!")

                            found = True
                            break
                    if not found:
                        mud.send_message(id, "scrap what?")

            if command == "bye":
                players[id]['target'] = None
                mud.send_message(id, "\n\r{} [%bold%yellow{} gold%reset] [%bold%red{} HP%reset] :> ".format(
                    players[id]['name'], players[id]['gold'], players[id]['health']), lineend="")
                continue

            mud.send_message(id, "\n\r{} -> {} [%bold%yellow{} gold%reset] [%bold%red{} HP%reset] :> ".format(
                players[id]['name'], players[id]['target']['name'], players[id]['gold'], players[id]['health']),
                lineend="")
        else:
            if command == "quit":
                mud.disconnect(id)
                continue

            # 'help' command
            elif command == "help":

                # send the player back the list of possible commands
                mud.send_message(id, "Commands:")
                mud.send_message(id, "  say <message>          - Says something out loud, "
                                 + "e.g. 'say Hello'")
                mud.send_message(id, "  look                   - Examines the "
                                 + "surroundings, e.g. 'look'")
                mud.send_message(id, "  examine <item>         - Examines an "
                                 + "item, e.g. 'examine fireplace'")
                mud.send_message(id, "  inventory              - Lists your inventory")
                mud.send_message(id, "  equip <item>           - Equip an "
                                 + "item, e.g. 'equip sword'")
                mud.send_message(id, "  unequip <weapon/armor> - Remove your currently "
                                 + "equipped weapon or armor")
                mud.send_message(id, "                           e.g. 'unequip weapon'")
                mud.send_message(id, "  take <item>            - Take an "
                                 + "item, e.g. 'take fireplace'")
                mud.send_message(id, "  drop <item>            - Destroy an inventory "
                                 + "item")
                mud.send_message(id, "  go <exit>              - Moves through the exit "
                                 + "specified, e.g. 'go outside'")
                mud.send_message(id, "  color <on/off>         - Turns color on or off, e.g. 'color off'")
                mud.send_message(id, "  quit                   - Disconnects from the game")

            # 'say' command
            elif command == "say":

                # go through every player in the game
                for pid, pl in players.items():
                    # if they're in the same room as the player
                    if players[pid]["room"] == players[id]["room"]:
                        # send them a message telling them what the player said
                        mud.send_message(pid, "%bold%blue{} says: {}".format(
                            players[id]["name"], params))

            elif command == 'color':
                ex = params.lower()
                if ex == "off":
                    if players[id]['color']:
                        putattrib(players[id]["dbid"], "color", "False")
                        mud.togglecolor(id)
                        players[id]['color'] = False
                else:
                    if not players[id]['color']:
                        putattrib(players[id]["dbid"], "color", "True")
                        mud.togglecolor(id)
                        players[id]['color'] = True

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
                if players[id]['weapon'] is not None:
                    mud.send_message(id, "%greenYour Weapon: %reset{}".format(players[id]['weapon']['name']))
                else:
                    mud.send_message(id, "%greenYour Weapon: %resetNone")
                if players[id]['armor'] is not None:
                    mud.send_message(id, "%greenYour Armor: %reset{}".format(players[id]['armor']['name']))
                else:
                    mud.send_message(id, "%greenYour Armor: %resetNone")
                mud.send_message(id, "%greenYour Inventory:")
                for item in players[id]['inventory']:
                    mud.send_message(id, " - {}".format(item['name']))

            elif command == "unequip":
                ex = params.lower()
                if ex == "armor":
                    if players[id]['armor'] is not None:
                        mud.send_message(id, "You remove your {}".format(players[id]['armor']['name']))
                        players[id]['inventory'].append(players[id]['armor'])
                        addinventory(players[id]['dbid'], players[id]['armor']['id'])
                        putattrib(players[id]['dbid'], "armor", "0")
                    else:
                        mud.send_message(id, "%redYou're not wearing any armor!")
                elif ex == "weapon":
                    if players[id]['weapon'] is not None:
                        mud.send_message(id, "You remove your {}".format(players[id]['weapon']['name']))
                        players[id]['inventory'].append(players[id]['weapon'])
                        addinventory(players[id]['dbid'], players[id]['weapon']['id'])
                        putattrib(players[id]['dbid'], "weapon", "0")
                    else:
                        mud.send_message(id, "%redYou're not wielding a weapon!")
                else:
                    mud.send_message(id, "Parameter must be either 'weapon' or 'armor'")
            elif command == "equip":
                ex = params.lower()
                found = False
                for it in players[id]['inventory']:
                    if it['name'] == ex:
                        found = True
                        if it['isarmor']:
                            if players[id]['armor'] is not None:
                                players[id]['inventory'].append(players[id]['armor'])
                                addinventory(players[id]['dbid'], players[id]['armor']['id'])
                            players[id]['armor'] = it
                            putattrib(players[id]['dbid'], "armor", it['id'])
                            delinventory(players[id]['dbid'], it['id'])
                            mud.send_message(id, "You equip your {}".format(it['name']))
                            players[id]['inventory'].remove(it)
                        elif it['isweapon']:
                            if players[id]['weapon'] is not None:
                                players[id]['inventory'].append(players[id]['weapon'])
                                addinventory(players[id]['dbid'], players[id]['weapon']['id'])
                            players[id]['weapon'] = it
                            putattrib(players[id]['dbid'], "weapon", it['id'])
                            delinventory(players[id]['dbid'], it['id'])
                            mud.send_message(id, "You equip your {}".format(it['name']))
                            players[id]['inventory'].remove(it)

                        else:
                            mud.send_message(id, "That item is not able to be equipped")
                        break

                if not found:
                    mud.send_message(id, "equip what?!")
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
                    for it in rm['npcs']:
                        if it['name'] == ex:
                            mud.send_message(id, it['description'])
                            found = True
                            break

                if not found:
                    mud.send_message(id, "examine what?!")

            elif command == "look":
                # store the player's current room
                rm = findroom(players[id]["room"])

                cmd_look(id, rm)

            # 'go' command
            elif command == "go":

                # store the exit name
                ex = params.lower()

                # store the player's current room
                rm = findroom(players[id]["room"])
                found = False
                # if the specified exit is found in the room's exits list
                for rex in rm["exits"]:
                    if rex["name"].lower() == ex:
                        found = True
                        key = True
                        if rex['itemkey'] != 0:
                            key = False
                            for ite in players[id]['inventory']:
                                if ite['id'] == rex['itemkey']:
                                    key = True
                                    break
                        if key:
                            # go through all the players in the game
                            for pid, pl in players.items():
                                # if player is in the same room and isn't the player
                                # sending the command
                                if players[pid]["room"] == players[id]["room"] \
                                        and pid != id:
                                    # send them a message telling them that the player
                                    # left the room
                                    mud.send_message(pid, "%bold%yellow{} left via exit '{}'".format(
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
                                                     "%bold%yellow{} arrived via exit '{}'".format(
                                                         players[id]["name"], rex["name"]))

                            # send the player a message telling them where they are now
                            mud.send_message(id, "You arrive at '{}'".format(
                                findroom(players[id]["room"])["name"]))

                            updateplayerroom(players[id])
                        else:
                            mud.send_message(id, "{}".format(rex['failkey']))
                    # the specified exit wasn't found in the current room
                if not found:
                    # send back an 'unknown exit' message
                    mud.send_message(id, "Unknown exit '{}'".format(ex))
            elif command == 'target':
                ex = params.lower()
                rm = findroom(players[id]["room"])
                found = False

                for it in rm['npcs']:
                    if it['name'] == ex:
                        players[id]['target'] = it
                        mud.send_message(id, "Now targeting %bold{}%reset enter 'bye' to stop targeting.".format(
                            it['name']))
                        found = True
                        break
                if not found:
                    mud.send_message(id, "I see no such NPC")
            # some other, unrecognised command
            else:
                # send back an 'unknown command' message
                mud.send_message(id, "Unknown command '{}'".format(command))
            if players[id]['target'] is not None:
                mud.send_message(id, "\n\r{} -> {} [%bold%yellow{} gold%reset] [%bold%red{} HP%reset] :> ".format(
                    players[id]['name'], players[id]['target']['name'], players[id]['gold'], players[id]['health']),
                                 lineend="")
            else:
                mud.send_message(id, "\n\r{} [%bold%yellow{} gold%reset] [%bold%red{} HP%reset] :> ".format(
                    players[id]['name'], players[id]['gold'], players[id]['health']), lineend="")
