import json
import re
import sys
from os import path, stat
from time import sleep

import gspread


def pathFileExists(filename):
    return path.exists(filename)


def getFileData(filename):
    result = []

    with open(filename, 'r') as openReadFile:
        for line in openReadFile:
            if "Characters" in line:
                return result
            result.append(line.strip())


def getConfigData(filename):
    configFileData = [i.strip() for i in open(filename, 'r')]
    return (configFileData[1], configFileData[4], configFileData[7], configFileData[10], configFileData[13:])


def getPlayersData(nicknames, boostFileData):
    result = []
    patternSearch = '(\d+)'

    for nickname in nicknames:
        nicknameObjectIndex = boostFileData.index(''.join(['["unit"] = "', nickname, '",']))
        result.append([re.search(patternSearch, boostFileData[nicknameObjectIndex - 3]).group(0),
                       re.search(patternSearch, boostFileData[nicknameObjectIndex - 1]).group(0),
                       nickname,
                       re.search(patternSearch, boostFileData[nicknameObjectIndex + 1]).group(0)])

    return result


def readFile(filename):
    with open(filename, "r") as read_file:
        return json.load(read_file)


def writeFile(filename, data):
    with open(filename, "w") as write_file:
        json.dump(data, write_file)


def getChangedPlayers(playersData):
    LOCAL_FILE = "boostData.json"
    flag = False

    if pathFileExists(LOCAL_FILE):
        jsonData = readFile(LOCAL_FILE)

        if len(jsonData) != len(playersData):
            writeFile(LOCAL_FILE, playersData)
            return playersData

        for i, v in enumerate(playersData):
            if v != jsonData[i]:
                flag = True
                jsonData[i] = v
            else:
                playersData[i] = None

        if flag:
            writeFile(LOCAL_FILE, jsonData)
            return [i for i in playersData if i != None]
        else:
            return None

    else:
        writeFile(LOCAL_FILE, playersData)
        return playersData


def updateGoogleSheet(service_account_filename, table_name, sheet_name, playersData, nicknames):
    gc = gspread.service_account(filename=service_account_filename)
    sh = gc.open(table_name)
    worksheet = sh.worksheet(sheet_name)

    if worksheet.get('A2').first():
        for player in playersData:
            playerRow = worksheet.find(player[2])

            if playerRow:
                playerRow = playerRow.row
            else:
                playerRow = nicknames.index(player[2]) + 2

            worksheet.update(f'A{playerRow}:E{playerRow}', [[i for i in player]])

    else:
        lastIndex = 2
        for player in playersData:
            worksheet.update(f'A{lastIndex}:E{lastIndex}', [[i for i in player]])
            lastIndex += 1


if __name__ == "__main__":
    CONFIG_FILE = "playersInfo.txt"

    if pathFileExists(CONFIG_FILE):
        BOOST_FILE, SERVICE_ACCOUNT_FILE, TABLE_NAME, SHEET_NAME, NICKNAMES = getConfigData(CONFIG_FILE)
    else:
        print("NO CONFIG_FILE")
        sys.exit()

    if pathFileExists(BOOST_FILE):
        lastUpdateTime = stat(BOOST_FILE).st_mtime
        while True:
            if lastUpdateTime != stat(BOOST_FILE).st_mtime:
                lastUpdateTime = stat(BOOST_FILE).st_mtime
                sleep(0.01)

                boostFileData = getFileData(BOOST_FILE)
                playersData = getPlayersData(NICKNAMES, boostFileData)
                changedPlayers = getChangedPlayers(playersData[:])

                if changedPlayers:
                    updateGoogleSheet(SERVICE_ACCOUNT_FILE, TABLE_NAME, SHEET_NAME, changedPlayers, NICKNAMES)

            continue

    else:
        print("NO BOOST_FILE")
        sys.exit()
