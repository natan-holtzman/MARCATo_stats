# -*- coding: utf-8 -*-
"""
Created on Sun Aug  9 11:46:58 2020

@author: natan
"""

import pandas as pd
#%%
#reformat the original buzzpoint data to remove extra quotation marks
file1 = open('questions-2.csv', 'r') 
Lines = file1.readlines() 

fixlines = [x.strip().strip(',').replace('"','') for x in Lines]
linelists = [x.split(';') for x in fixlines]

file1.close()

#turn the data into a Pandas dataframe
rawdata = pd.DataFrame(data=linelists[1:],columns=linelists[0])
rawdata.loc[rawdata['BuzzTime'] == 'NULL', 'BuzzTime'] = '9999'
rawdata = rawdata.astype({'RoundNumber':int, 'QuestionNumber':int, 'BuzzTime':float})
rawdata.to_csv('all_rounds_buzzes2.csv')

#%%
#load the formatted data
rawdata = pd.read_csv('all_rounds_buzzes2.csv')
teams = pd.unique(rawdata['TeamName'])
players = pd.unique(rawdata['PlayerName'])
#%%
#sort by buzz time so the first buzz will be first in the data
rawdata = rawdata.sort_values('BuzzTime')
#%%

#%%
def judge_tu(qsort):
    team_result = {}
    player_result = {}
    #if the first buzz is correct
    if qsort['IsCorrect'].iloc[0] == 'Correct':
        #if the first two buzzes are tied in terms of buzz time, and both correct
        #split the points between each team/player
        #otherwise, give the buzz entirely to one team/player

        if len(qsort) > 1:
            if qsort['IsCorrect'].iloc[1]== 'Correct' and qsort['BuzzTime'].iloc[0]==qsort['BuzzTime'].iloc[1]:
                team_result[qsort['TeamName'].iloc[0]] = 5; player_result[qsort['PlayerName'].iloc[0]] = 5
                team_result[qsort['TeamName'].iloc[1]] = 5; player_result[qsort['PlayerName'].iloc[1]] = 5
            else:
                team_result[qsort['TeamName'].iloc[0]] = 10; player_result[qsort['PlayerName'].iloc[0]] = 10
        else:     
            team_result[qsort['TeamName'].iloc[0]] = 10; player_result[qsort['PlayerName'].iloc[0]] = 10
    #if the first buzz is incorrect
    else:
        #if it's before 60 seconds, give that player a neg, otherwise we don't need to update that player/team score
        if qsort['BuzzTime'].iloc[0] < 60:
            team_result[qsort['TeamName'].iloc[0]] = -5; player_result[qsort['PlayerName'].iloc[0]] = -5
        #get the buzzes from the team that is not locked out
        otherteam = qsort.loc[qsort['TeamName'] != qsort['TeamName'].iloc[0]]#.reset_index()
        #if the other team buzzed
        if len(otherteam) > 0:
            #if the remaining team has at least one correct buzz
            if sum(otherteam['IsCorrect']=='Correct') > 0:
                #credit that team with 10 points
                team_result[otherteam['TeamName'].iloc[0]] = 10
                #credit the first player on that team to buzz correctly with 10 points
                if otherteam['IsCorrect'].iloc[0] == 'Correct':
                    player_result[otherteam['PlayerName'].iloc[0]] = 10
                else:
                    player_result[otherteam['PlayerName'].iloc[1]] = 10
    return (team_result, player_result)
#%%
def simgame(t1,t2,gameset):
    #gameset = rawdata[rawdata['RoundNumber']==rnd]
    gamebuzz = gameset.loc[gameset['TeamName'].isin([t1,t2])]
    teamscores = {t1:0,t2:0}
    playerscores = {}
    for pn in pd.unique(gamebuzz['PlayerName']):
        playerscores[pn] = 0
    for qn in range(1,21):
        qtab = gamebuzz.loc[gamebuzz['QuestionNumber']==qn]
        (team_result, player_result) = judge_tu(qtab)
        for t in team_result.keys():
            teamscores[t] += team_result[t]
        for p in player_result.keys():
            playerscores[p] += player_result[p]
    return (teamscores, playerscores)
#%%
#we will store the results in several dictionaries
team_scores = dict(zip(teams,[0]*len(teams)))
player_scores = dict(zip(players,[0]*len(players)))
team_wins = dict(zip(teams,[0]*len(teams)))
team_losses = dict(zip(teams,[0]*len(teams)))
team_ties = dict(zip(teams,[0]*len(teams)))
#%%
nteams = 36
for rnd in range(1,13):
    print(rnd)
    rndgames = rawdata.loc[rawdata['RoundNumber']==rnd]
    for i in range(0,nteams-1):
        ti = teams[i]
        for j in range(i+1, nteams):
            tj = teams[j]
            (teamscoresIJ, playerscoresIJ) = simgame(ti,tj,rndgames)
            #print (i,j, 'Score: ', teamscoresIJ.values())
            for t in teamscoresIJ.keys():
                team_scores[t] += teamscoresIJ[t]
            for p in playerscoresIJ.keys():
                player_scores[p] += playerscoresIJ[p]
            match_score = list(teamscoresIJ.items())
            if match_score[0][1] == match_score[1][1]:
                team_ties[ti] += 1
                team_ties[tj] += 1
                #print('Tie')
            elif match_score[0][1] > match_score[1][1]:
                team_wins[match_score[0][0]] += 1
                team_losses[match_score[1][0]] += 1
                #print(match_score[0][0],' Win')
            else:
                team_losses[match_score[0][0]] += 1
                team_wins[match_score[1][0]] += 1
                #print(match_score[1][0],' Win')

#%%
#function to convert dictionary to data frame
def d2df(d,c1,c2):
    dlist = list(d.items())
    mykeys = [x[0] for x in dlist]
    myvalues = [x[1] for x in dlist]
    mydf  = pd.DataFrame({c1:mykeys,c2:myvalues})
    return mydf
#%%
    
team_scores2 = d2df(team_scores,'Team','PPG')
player_scores2 = d2df(player_scores,'player','PPG')
team_wins2 = d2df(team_wins,'Team','Wins')
team_losses2 = d2df(team_losses,'Team','Losses')
team_ties2 = d2df(team_ties,'Team','Ties')
#%%
#convert total points to points per game, each team having played 35*12 games
gamesperteam = 35*12
team_scores2['PPG'] /= gamesperteam
player_scores2['PPG'] /= gamesperteam

#%%
#make a dict that links teams to players
players = []
for t in teams:
    tplayer = pd.unique(rawdata[rawdata['TeamName']==t]['PlayerName'])
    players.append(', '.join(tplayer))
teamplayer = pd.DataFrame({'Team':teams,'Player':players})
#%%
team_record = pd.merge(team_wins2, team_losses2, how='outer',on='Team')
team_record = pd.merge(team_record, team_ties2, how='outer',on='Team')
team_record = pd.merge(team_record, teamplayer, how='left',on='Team')
#%%
player_scores2 = player_scores2.sort_values(by='PPG',ascending=False)
player_scores2['Rank'] = list(range(1,len(player_scores2)+1))

player_scores2.to_csv('Player_Points_all_v2.csv')
#%%
team_stats = pd.merge(team_record, team_scores2,how='left',on='Team')
team_stats = team_stats.sort_values(by=['Wins','Ties','PPG'],ascending=False)
team_stats['Rank'] = list(range(1,37))
#%%
team_stats.to_csv('Team_Stats_all_v2.csv')
#%%
