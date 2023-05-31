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
     mycursor.execute("SELECT objid FROM roominv WHERE roomid = %s", (room['id'], ))
     myresult = mycursor.fetchall()
     for row in myresult:
         mycursor.execute("SELECT name, description FROM objdef WHERE id = %s", (row[0], ))
         objrow = mycursor.fetchone()
         room['items'].append({'id': row[0], 'name': objrow[0], 'description': objrow[1]})


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
        room = {'id': row[0], 'name' : row[1], 'description': row[2], 'exits': [], 'items': []}
        mycursor.execute("SELECT id, name, toroom FROM exitdef WHERE fromroom = %s", (row[0],))
        exresult = mycursor.fetchall()

        for exrow in exresult:
            room['exits'].append({'name': exrow[1], 'toroom': exrow[2]})

        rooms.append(room)

    return rooms


# structure defining the rooms in the game. Try adding more rooms to the game!
# rooms = {
#    "Tavern": {
#        "description": "You're in a cozy tavern warmed by an open fire.",
#        "exits": {"outside": "Outside"},
#    },
#    "Outside": {
#        "description": "You're standing outside a tavern. It's raining.",
#        "exits": {"inside": "Tavern"},
#    }
# }

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
        del(players[id])

    # go through any new commands sent from players
    for id, command, params in mud.get_commands():

        # if for any reason the player isn't in the player map, skip them and
        # move on to the next one
        if id not in players:
            continue

        # if the player hasn't given their name yet, use this first command as
        # their name and move them to the starting room.
        if players[id]["name"] is None:

            players[id]["name"] = command
            players[id]["room"] = 1

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

        # 'help' command
        elif command == "help":

            # send the player back the list of possible commands
            mud.send_message(id, "Commands:")
            mud.send_message(id, "  say <message>  - Says something out loud, "
                                 + "e.g. 'say Hello'")
            mud.send_message(id, "  look           - Examines the "
                                 + "surroundings, e.g. 'look'")
            mud.send_message(id, "  go <exit>      - Moves through the exit "
                                 + "specified, e.g. 'go outside'")

        # 'say' command
        elif command == "say":

            # go through every player in the game
            for pid, pl in players.items():
                # if they're in the same room as the player
                if players[pid]["room"] == players[id]["room"]:
                    # send them a message telling them what the player said
                    mud.send_message(pid, "{} says: {}".format(
                                                players[id]["name"], params))

        # 'look' command
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
                # the specified exit wasn't found in the current room
            if not found:
                # send back an 'unknown exit' message
                mud.send_message(id, "Unknown exit '{}'".format(ex))

        # some other, unrecognised command
        else:
            # send back an 'unknown command' message
            mud.send_message(id, "Unknown command '{}'".format(command))
