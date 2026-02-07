import streamlit as st
import re
import html
import requests
import json
import random
import pandas as pd
from datetime import datetime

# Demo 資料：真實比賽紀錄 (36 手牌，內嵌於 app.py)
DEMO_HANDS_TEXT = """
Poker Hand #TM5544469446: Tournament #258198994, $25 GGMasters Bounty Warm-Up Special Hold'em No Limit - Level12(200/400) - 2026/02/04 01:07:12
Table '380' 8-max Seat #3 is the button
Seat 1: 4b92a21c (13,785 in chips)
Seat 2: db2c203e (14,470 in chips)
Seat 3: 511f4d1c (18,274 in chips)
Seat 4: f113568e (7,311 in chips)
Seat 5: Hero (5,822 in chips)
Seat 6: e03b1647 (17,193 in chips)
Seat 7: 56b0137c (28,245 in chips)
Seat 8: cb195c66 (49,475 in chips)
511f4d1c: posts the ante 50
e03b1647: posts the ante 50
f113568e: posts the ante 50
db2c203e: posts the ante 50
56b0137c: posts the ante 50
Hero: posts the ante 50
4b92a21c: posts the ante 50
cb195c66: posts the ante 50
f113568e: posts small blind 200
Hero: posts big blind 400
*** HOLE CARDS ***
Dealt to 4b92a21c 
Dealt to db2c203e 
Dealt to 511f4d1c 
Dealt to f113568e 
Dealt to Hero [4d 8d]
Dealt to e03b1647 
Dealt to 56b0137c 
Dealt to cb195c66 
e03b1647: raises 400 to 800
56b0137c: folds
cb195c66: folds
4b92a21c: folds
db2c203e: folds
511f4d1c: folds
f113568e: folds
Hero: calls 400
*** FLOP *** [Kd 4s 8s]
Hero: checks
e03b1647: bets 926
Hero: raises 4,046 to 4,972 and is all-in
e03b1647: calls 4,046
Hero: shows [4d 8d] (two pair, Eights and Fours)
e03b1647: shows [Td Tc] (a pair of Tens)
*** TURN *** [Kd 4s 8s] [7c]
*** RIVER *** [Kd 4s 8s 7c] [Ts]
*** SHOWDOWN ***
e03b1647 collected 12,144 from pot
*** SUMMARY ***
Total pot 12,144 | Rake 0 | Jackpot 0 | Bingo 0 | Fortune 0 | Tax 0
Board [Kd 4s 8s 7c Ts]
Seat 1: 4b92a21c folded before Flop
Seat 2: db2c203e folded before Flop
Seat 3: 511f4d1c (button) folded before Flop
Seat 4: f113568e (small blind) folded before Flop
Seat 5: Hero (big blind) showed [4d 8d] and lost with two pair, Eights and Fours
Seat 6: e03b1647 showed [Td Tc] and won (12,144) with three of a kind, Tens
Seat 7: 56b0137c folded before Flop
Seat 8: cb195c66 folded before Flop


Poker Hand #TM5544469412: Tournament #258198994, $25 GGMasters Bounty Warm-Up Special Hold'em No Limit - Level12(200/400) - 2026/02/04 01:06:46
Table '380' 8-max Seat #2 is the button
Seat 1: 4b92a21c (13,835 in chips)
Seat 2: db2c203e (14,520 in chips)
Seat 3: 511f4d1c (18,524 in chips)
Seat 4: f113568e (6,761 in chips)
Seat 5: Hero (5,872 in chips)
Seat 6: e03b1647 (17,243 in chips)
Seat 7: 56b0137c (28,295 in chips)
Seat 8: cb195c66 (49,525 in chips)
e03b1647: posts the ante 50
511f4d1c: posts the ante 50
f113568e: posts the ante 50
db2c203e: posts the ante 50
56b0137c: posts the ante 50
Hero: posts the ante 50
4b92a21c: posts the ante 50
cb195c66: posts the ante 50
511f4d1c: posts small blind 200
f113568e: posts big blind 400
*** HOLE CARDS ***
Dealt to 4b92a21c 
Dealt to db2c203e 
Dealt to 511f4d1c 
Dealt to f113568e 
Dealt to Hero [5c 7c]
Dealt to e03b1647 
Dealt to 56b0137c 
Dealt to cb195c66 
Hero: folds
e03b1647: folds
56b0137c: folds
cb195c66: folds
4b92a21c: folds
db2c203e: folds
511f4d1c: folds
Uncalled bet (200) returned to f113568e
*** SHOWDOWN ***
f113568e collected 800 from pot
*** SUMMARY ***
Total pot 800 | Rake 0 | Jackpot 0 | Bingo 0 | Fortune 0 | Tax 0
Seat 1: 4b92a21c folded before Flop
Seat 2: db2c203e (button) folded before Flop
Seat 3: 511f4d1c (small blind) folded before Flop
Seat 4: f113568e (big blind) collected (800)
Seat 5: Hero folded before Flop
Seat 6: e03b1647 folded before Flop
Seat 7: 56b0137c folded before Flop
Seat 8: cb195c66 folded before Flop


Poker Hand #TM5544469296: Tournament #258198994, $25 GGMasters Bounty Warm-Up Special Hold'em No Limit - Level11(175/350) - 2026/02/04 01:04:59
Table '380' 8-max Seat #1 is the button
Seat 1: 4b92a21c (13,880 in chips)
Seat 2: db2c203e (14,740 in chips)
Seat 3: 511f4d1c (22,116 in chips)
Seat 4: f113568e (6,806 in chips)
Seat 5: Hero (5,917 in chips)
Seat 6: e03b1647 (13,206 in chips)
Seat 7: 56b0137c (28,340 in chips)
Seat 8: cb195c66 (49,570 in chips)
e03b1647: posts the ante 45
511f4d1c: posts the ante 45
f113568e: posts the ante 45
db2c203e: posts the ante 45
56b0137c: posts the ante 45
Hero: posts the ante 45
4b92a21c: posts the ante 45
cb195c66: posts the ante 45
db2c203e: posts small blind 175
511f4d1c: posts big blind 350
*** HOLE CARDS ***
Dealt to 4b92a21c 
Dealt to db2c203e 
Dealt to 511f4d1c 
Dealt to f113568e 
Dealt to Hero [4s Qd]
Dealt to e03b1647 
Dealt to 56b0137c 
Dealt to cb195c66 
f113568e: folds
Hero: folds
e03b1647: raises 350 to 700
56b0137c: folds
cb195c66: folds
4b92a21c: folds
db2c203e: folds
511f4d1c: raises 1,575 to 2,275
e03b1647: calls 1,575
*** FLOP *** [Jd 4h 4c]
511f4d1c: bets 1,272
e03b1647: calls 1,272
*** TURN *** [Jd 4h 4c] [7h]
511f4d1c: checks
e03b1647: checks
*** RIVER *** [Jd 4h 4c 7h] [Ts]
511f4d1c: checks
e03b1647: checks
511f4d1c: shows [Kh Ah] (a pair of Fours)
e03b1647: shows [5s 5d] (two pair, Fives and Fours)
*** SHOWDOWN ***
e03b1647 collected 7,629 from pot
*** SUMMARY ***
Total pot 7,629 | Rake 0 | Jackpot 0 | Bingo 0 | Fortune 0 | Tax 0
Board [Jd 4h 4c 7h Ts]
Seat 1: 4b92a21c (button) folded before Flop
Seat 2: db2c203e (small blind) folded before Flop
Seat 3: 511f4d1c (big blind) showed [Kh Ah] and lost with a pair of Fours
Seat 4: f113568e folded before Flop
Seat 5: Hero folded before Flop
Seat 6: e03b1647 showed [5s 5d] and won (7,629) with two pair, Fives and Fours
Seat 7: 56b0137c folded before Flop
Seat 8: cb195c66 folded before Flop


Poker Hand #TM5544469182: Tournament #258198994, $25 GGMasters Bounty Warm-Up Special Hold'em No Limit - Level11(175/350) - 2026/02/04 01:03:22
Table '380' 8-max Seat #8 is the button
Seat 1: 4b92a21c (14,100 in chips)
Seat 2: db2c203e (15,135 in chips)
Seat 3: 511f4d1c (22,161 in chips)
Seat 4: f113568e (6,851 in chips)
Seat 5: Hero (5,962 in chips)
Seat 6: e03b1647 (13,251 in chips)
Seat 7: 56b0137c (21,019 in chips)
Seat 8: cb195c66 (56,096 in chips)
e03b1647: posts the ante 45
511f4d1c: posts the ante 45
f113568e: posts the ante 45
db2c203e: posts the ante 45
56b0137c: posts the ante 45
Hero: posts the ante 45
cb195c66: posts the ante 45
4b92a21c: posts the ante 45
4b92a21c: posts small blind 175
db2c203e: posts big blind 350
*** HOLE CARDS ***
Dealt to 4b92a21c 
Dealt to db2c203e 
Dealt to 511f4d1c 
Dealt to f113568e 
Dealt to Hero [2c Th]
Dealt to e03b1647 
Dealt to 56b0137c 
Dealt to cb195c66 
511f4d1c: folds
f113568e: folds
Hero: folds
e03b1647: folds
56b0137c: raises 350 to 700
cb195c66: calls 700
4b92a21c: folds
db2c203e: folds
*** FLOP *** [8s 6s Ah]
56b0137c: bets 755
cb195c66: calls 755
*** TURN *** [8s 6s Ah] [Tc]
56b0137c: bets 2,718
cb195c66: calls 2,718
*** RIVER *** [8s 6s Ah Tc] [7d]
56b0137c: bets 2,308
cb195c66: calls 2,308
56b0137c: shows [9s Ac] (a straight, Ten to Six)
cb195c66: shows [7h 5h] (a pair of Sevens)
*** SHOWDOWN ***
56b0137c collected 13,847 from pot
*** SUMMARY ***
Total pot 13,847 | Rake 0 | Jackpot 0 | Bingo 0 | Fortune 0 | Tax 0
Board [8s 6s Ah Tc 7d]
Seat 1: 4b92a21c (small blind) folded before Flop
Seat 2: db2c203e (big blind) folded before Flop
Seat 3: 511f4d1c folded before Flop
Seat 4: f113568e folded before Flop
Seat 5: Hero folded before Flop
Seat 6: e03b1647 folded before Flop
Seat 7: 56b0137c showed [9s Ac] and won (13,847) with a straight, Ten to Six
Seat 8: cb195c66 (button) showed [7h 5h] and lost with a pair of Sevens


Poker Hand #TM5544469098: Tournament #258198994, $25 GGMasters Bounty Warm-Up Special Hold'em No Limit - Level11(175/350) - 2026/02/04 00:54:56
Table '380' 8-max Seat #7 is the button
Seat 1: 4b92a21c (14,495 in chips)
Seat 2: db2c203e (15,180 in chips)
Seat 3: 511f4d1c (22,206 in chips)
Seat 4: f113568e (6,896 in chips)
Seat 5: Hero (6,007 in chips)
Seat 6: e03b1647 (25,896 in chips)
Seat 7: 56b0137c (21,064 in chips)
Seat 8: cb195c66 (42,831 in chips)
e03b1647: posts the ante 45
511f4d1c: posts the ante 45
f113568e: posts the ante 45
db2c203e: posts the ante 45
56b0137c: posts the ante 45
Hero: posts the ante 45
4b92a21c: posts the ante 45
cb195c66: posts the ante 45
cb195c66: posts small blind 175
4b92a21c: posts big blind 350
*** HOLE CARDS ***
Dealt to 4b92a21c 
Dealt to db2c203e 
Dealt to 511f4d1c 
Dealt to f113568e 
Dealt to Hero [3d Ks]
Dealt to e03b1647 
Dealt to 56b0137c 
Dealt to cb195c66 
db2c203e: folds
511f4d1c: folds
f113568e: folds
Hero: folds
e03b1647: raises 350 to 700
56b0137c: folds
cb195c66: calls 525
4b92a21c: folds
*** FLOP *** [3s Ah 5c]
cb195c66: checks
e03b1647: bets 1,050
cb195c66: calls 1,050
*** TURN *** [3s Ah 5c] [Qh]
cb195c66: checks
e03b1647: bets 2,625
cb195c66: calls 2,625
*** RIVER *** [3s Ah 5c Qh] [8h]
cb195c66: checks
e03b1647: bets 8,225
cb195c66: calls 8,225
e03b1647: shows [7c Kc] (Ace high)
cb195c66: shows [Ad 9d] (a pair of Aces)
*** SHOWDOWN ***
cb195c66 collected 25,910 from pot
*** SUMMARY ***
Total pot 25,910 | Rake 0 | Jackpot 0 | Bingo 0 | Fortune 0 | Tax 0
Board [3s Ah 5c Qh 8h]
Seat 1: 4b92a21c (big blind) folded before Flop
Seat 2: db2c203e folded before Flop
Seat 3: 511f4d1c folded before Flop
Seat 4: f113568e folded before Flop
Seat 5: Hero folded before Flop
Seat 6: e03b1647 showed [7c Kc] and lost with Ace high
Seat 7: 56b0137c (button) folded before Flop
Seat 8: cb195c66 (small blind) showed [Ad 9d] and won (25,910) with a pair of Aces


Poker Hand #TM5543749068: Tournament #258198994, $25 GGMasters Bounty Warm-Up Special Hold'em No Limit - Level11(175/350) - 2026/02/04 00:54:25
Table '380' 8-max Seat #6 is the button
Seat 1: 4b92a21c (14,540 in chips)
Seat 2: db2c203e (15,225 in chips)
Seat 3: 511f4d1c (22,251 in chips)
Seat 4: f113568e (6,941 in chips)
Seat 5: Hero (6,052 in chips)
Seat 6: e03b1647 (25,056 in chips)
Seat 7: 56b0137c (21,284 in chips)
Seat 8: cb195c66 (43,226 in chips)
e03b1647: posts the ante 45
511f4d1c: posts the ante 45
f113568e: posts the ante 45
db2c203e: posts the ante 45
56b0137c: posts the ante 45
Hero: posts the ante 45
4b92a21c: posts the ante 45
cb195c66: posts the ante 45
56b0137c: posts small blind 175
cb195c66: posts big blind 350
*** HOLE CARDS ***
Dealt to 4b92a21c 
Dealt to db2c203e 
Dealt to 511f4d1c 
Dealt to f113568e 
Dealt to Hero [9c 3c]
Dealt to e03b1647 
Dealt to 56b0137c 
Dealt to cb195c66 
4b92a21c: folds
db2c203e: folds
511f4d1c: folds
f113568e: folds
Hero: folds
e03b1647: raises 525 to 875
56b0137c: folds
cb195c66: folds
Uncalled bet (525) returned to e03b1647
*** SHOWDOWN ***
e03b1647 collected 1,235 from pot
*** SUMMARY ***
Total pot 1,235 | Rake 0 | Jackpot 0 | Bingo 0 | Fortune 0 | Tax 0
Seat 1: 4b92a21c folded before Flop
Seat 2: db2c203e folded before Flop
Seat 3: 511f4d1c folded before Flop
Seat 4: f113568e folded before Flop
Seat 5: Hero folded before Flop
Seat 6: e03b1647 (button) collected (1,235)
Seat 7: 56b0137c (small blind) folded before Flop
Seat 8: cb195c66 (big blind) folded before Flop


Poker Hand #TM5543749023: Tournament #258198994, $25 GGMasters Bounty Warm-Up Special Hold'em No Limit - Level11(175/350) - 2026/02/04 00:53:57
Table '380' 8-max Seat #5 is the button
Seat 1: 4b92a21c (14,585 in chips)
Seat 2: db2c203e (15,270 in chips)
Seat 3: 511f4d1c (22,296 in chips)
Seat 4: f113568e (6,986 in chips)
Seat 5: Hero (6,097 in chips)
Seat 6: e03b1647 (25,451 in chips)
Seat 7: 56b0137c (20,619 in chips)
Seat 8: cb195c66 (43,271 in chips)
511f4d1c: posts the ante 45
e03b1647: posts the ante 45
f113568e: posts the ante 45
db2c203e: posts the ante 45
56b0137c: posts the ante 45
Hero: posts the ante 45
4b92a21c: posts the ante 45
cb195c66: posts the ante 45
e03b1647: posts small blind 175
56b0137c: posts big blind 350
*** HOLE CARDS ***
Dealt to 4b92a21c 
Dealt to db2c203e 
Dealt to 511f4d1c 
Dealt to f113568e 
Dealt to Hero [Qd 8h]
Dealt to e03b1647 
Dealt to 56b0137c 
Dealt to cb195c66 
cb195c66: folds
4b92a21c: folds
db2c203e: folds
511f4d1c: folds
f113568e: folds
Hero: folds
e03b1647: calls 175
56b0137c: raises 1,050 to 1,400
e03b1647: folds
Uncalled bet (1,050) returned to 56b0137c
*** SHOWDOWN ***
56b0137c collected 1,060 from pot
*** SUMMARY ***
Total pot 1,060 | Rake 0 | Jackpot 0 | Bingo 0 | Fortune 0 | Tax 0
Seat 1: 4b92a21c folded before Flop
Seat 2: db2c203e folded before Flop
Seat 3: 511f4d1c folded before Flop
Seat 4: f113568e folded before Flop
Seat 5: Hero (button) folded before Flop
Seat 6: e03b1647 (small blind) folded before Flop
Seat 7: 56b0137c (big blind) collected (1,060)
Seat 8: cb195c66 folded before Flop


Poker Hand #TM5543748942: Tournament #258198994, $25 GGMasters Bounty Warm-Up Special Hold'em No Limit - Level11(175/350) - 2026/02/04 00:52:42
Table '380' 8-max Seat #4 is the button
Seat 1: 4b92a21c (14,630 in chips)
Seat 2: db2c203e (15,315 in chips)
Seat 3: 511f4d1c (22,341 in chips)
Seat 4: f113568e (8,370 in chips)
Seat 5: Hero (6,317 in chips)
Seat 6: e03b1647 (23,622 in chips)
Seat 7: 56b0137c (20,664 in chips)
Seat 8: cb195c66 (43,316 in chips)
511f4d1c: posts the ante 45
e03b1647: posts the ante 45
f113568e: posts the ante 45
db2c203e: posts the ante 45
56b0137c: posts the ante 45
Hero: posts the ante 45
4b92a21c: posts the ante 45
cb195c66: posts the ante 45
Hero: posts small blind 175
e03b1647: posts big blind 350
*** HOLE CARDS ***
Dealt to 4b92a21c 
Dealt to db2c203e 
Dealt to 511f4d1c 
Dealt to f113568e 
Dealt to Hero [6s 2s]
Dealt to e03b1647 
Dealt to 56b0137c 
Dealt to cb195c66 
56b0137c: folds
cb195c66: folds
4b92a21c: folds
db2c203e: folds
511f4d1c: folds
f113568e: raises 350 to 700
Hero: folds
e03b1647: calls 350
*** FLOP *** [5h Ad 3h]
e03b1647: checks
f113568e: bets 639
e03b1647: calls 639
*** TURN *** [5h Ad 3h] [9s]
e03b1647: checks
f113568e: checks
*** RIVER *** [5h Ad 3h 9s] [6h]
e03b1647: bets 2,250
f113568e: folds
Uncalled bet (2,250) returned to e03b1647
*** SHOWDOWN ***
e03b1647 collected 3,213 from pot
*** SUMMARY ***
Total pot 3,213 | Rake 0 | Jackpot 0 | Bingo 0 | Fortune 0 | Tax 0
Board [5h Ad 3h 9s 6h]
Seat 1: 4b92a21c folded before Flop
Seat 2: db2c203e folded before Flop
Seat 3: 511f4d1c folded before Flop
Seat 4: f113568e (button) folded on the River
Seat 5: Hero (small blind) folded before Flop
Seat 6: e03b1647 (big blind) won (3,213)
Seat 7: 56b0137c folded before Flop
Seat 8: cb195c66 folded before Flop


Poker Hand #TM5543748842: Tournament #258198994, $25 GGMasters Bounty Warm-Up Special Hold'em No Limit - Level11(175/350) - 2026/02/04 00:51:21
Table '380' 8-max Seat #3 is the button
Seat 1: 4b92a21c (14,675 in chips)
Seat 2: db2c203e (15,360 in chips)
Seat 3: 511f4d1c (22,386 in chips)
Seat 4: f113568e (8,590 in chips)
Seat 5: Hero (8,380 in chips)
Seat 6: e03b1647 (24,367 in chips)
Seat 7: 56b0137c (20,709 in chips)
Seat 8: cb195c66 (40,108 in chips)
511f4d1c: posts the ante 45
e03b1647: posts the ante 45
f113568e: posts the ante 45
db2c203e: posts the ante 45
56b0137c: posts the ante 45
Hero: posts the ante 45
4b92a21c: posts the ante 45
cb195c66: posts the ante 45
f113568e: posts small blind 175
Hero: posts big blind 350
*** HOLE CARDS ***
Dealt to 4b92a21c 
Dealt to db2c203e 
Dealt to 511f4d1c 
Dealt to f113568e 
Dealt to Hero [Ah 6c]
Dealt to e03b1647 
Dealt to 56b0137c 
Dealt to cb195c66 
e03b1647: raises 350 to 700
56b0137c: folds
cb195c66: calls 700
4b92a21c: folds
db2c203e: folds
511f4d1c: folds
f113568e: folds
Hero: calls 350
*** FLOP *** [3c 9h 8d]
Hero: checks
e03b1647: checks
cb195c66: checks
*** TURN *** [3c 9h 8d] [2d]
Hero: bets 1,318
e03b1647: folds
cb195c66: calls 1,318
*** RIVER *** [3c 9h 8d 2d] [7c]
Hero: checks
cb195c66: checks
Hero: shows [Ah 6c] (Ace high)
cb195c66: shows [Ad 7d] (a pair of Sevens)
*** SHOWDOWN ***
cb195c66 collected 5,271 from pot
*** SUMMARY ***
Total pot 5,271 | Rake 0 | Jackpot 0 | Bingo 0 | Fortune 0 | Tax 0
Board [3c 9h 8d 2d 7c]
Seat 1: 4b92a21c folded before Flop
Seat 2: db2c203e folded before Flop
Seat 3: 511f4d1c (button) folded before Flop
Seat 4: f113568e (small blind) folded before Flop
Seat 5: Hero (big blind) showed [Ah 6c] and lost with Ace high
Seat 6: e03b1647 folded on the Turn
Seat 7: 56b0137c folded before Flop
Seat 8: cb195c66 showed [Ad 7d] and won (5,271) with a pair of Sevens


Poker Hand #TM5543748810: Tournament #258198994, $25 GGMasters Bounty Warm-Up Special Hold'em No Limit - Level11(175/350) - 2026/02/04 00:50:56
Table '380' 8-max Seat #2 is the button
Seat 1: 4b92a21c (14,720 in chips)
Seat 2: db2c203e (15,405 in chips)
Seat 3: 511f4d1c (22,606 in chips)
Seat 4: f113568e (8,985 in chips)
Seat 5: Hero (8,425 in chips)
Seat 6: e03b1647 (24,412 in chips)
Seat 7: 56b0137c (20,754 in chips)
Seat 8: cb195c66 (39,268 in chips)
e03b1647: posts the ante 45
511f4d1c: posts the ante 45
f113568e: posts the ante 45
db2c203e: posts the ante 45
56b0137c: posts the ante 45
Hero: posts the ante 45
4b92a21c: posts the ante 45
cb195c66: posts the ante 45
511f4d1c: posts small blind 175
f113568e: posts big blind 350
*** HOLE CARDS ***
Dealt to 4b92a21c 
Dealt to db2c203e 
Dealt to 511f4d1c 
Dealt to f113568e 
Dealt to Hero [6c 4s]
Dealt to e03b1647 
Dealt to 56b0137c 
Dealt to cb195c66 
Hero: folds
e03b1647: folds
56b0137c: folds
cb195c66: raises 700 to 1,050
4b92a21c: folds
db2c203e: folds
511f4d1c: folds
f113568e: folds
Uncalled bet (700) returned to cb195c66
*** SHOWDOWN ***
cb195c66 collected 1,235 from pot
*** SUMMARY ***
Total pot 1,235 | Rake 0 | Jackpot 0 | Bingo 0 | Fortune 0 | Tax 0
Seat 1: 4b92a21c folded before Flop
Seat 2: db2c203e (button) folded before Flop
Seat 3: 511f4d1c (small blind) folded before Flop
Seat 4: f113568e (big blind) folded before Flop
Seat 5: Hero folded before Flop
Seat 6: e03b1647 folded before Flop
Seat 7: 56b0137c folded before Flop
Seat 8: cb195c66 collected (1,235)


Poker Hand #TM5543748767: Tournament #258198994, $25 GGMasters Bounty Warm-Up Special Hold'em No Limit - Level11(175/350) - 2026/02/04 00:50:12
Table '380' 8-max Seat #1 is the button
Seat 1: 4b92a21c (11,255 in chips)
Seat 2: db2c203e (18,250 in chips)
Seat 3: 511f4d1c (23,001 in chips)
Seat 4: f113568e (9,030 in chips)
Seat 5: Hero (8,470 in chips)
Seat 6: e03b1647 (24,457 in chips)
Seat 7: 56b0137c (20,799 in chips)
Seat 8: cb195c66 (39,313 in chips)
e03b1647: posts the ante 45
511f4d1c: posts the ante 45
f113568e: posts the ante 45
db2c203e: posts the ante 45
56b0137c: posts the ante 45
Hero: posts the ante 45
4b92a21c: posts the ante 45
cb195c66: posts the ante 45
db2c203e: posts small blind 175
511f4d1c: posts big blind 350
*** HOLE CARDS ***
Dealt to 4b92a21c 
Dealt to db2c203e 
Dealt to 511f4d1c 
Dealt to f113568e 
Dealt to Hero [4h Ts]
Dealt to e03b1647 
Dealt to 56b0137c 
Dealt to cb195c66 
f113568e: folds
Hero: folds
e03b1647: folds
56b0137c: folds
cb195c66: folds
4b92a21c: raises 350 to 700
db2c203e: raises 2,100 to 2,800
511f4d1c: folds
4b92a21c: raises 8,410 to 11,210 and is all-in
db2c203e: folds
Uncalled bet (8,410) returned to 4b92a21c
*** SHOWDOWN ***
4b92a21c collected 6,310 from pot
*** SUMMARY ***
Total pot 6,310 | Rake 0 | Jackpot 0 | Bingo 0 | Fortune 0 | Tax 0
Seat 1: 4b92a21c (button) collected (6,310)
Seat 2: db2c203e (small blind) folded before Flop
Seat 3: 511f4d1c (big blind) folded before Flop
Seat 4: f113568e folded before Flop
Seat 5: Hero folded before Flop
Seat 6: e03b1647 folded before Flop
Seat 7: 56b0137c folded before Flop
Seat 8: cb195c66 folded before Flop


Poker Hand #TM5543748688: Tournament #258198994, $25 GGMasters Bounty Warm-Up Special Hold'em No Limit - Level11(175/350) - 2026/02/04 00:49:05
Table '380' 8-max Seat #8 is the button
Seat 1: 4b92a21c (11,475 in chips)
Seat 2: db2c203e (28,427 in chips)
Seat 3: 511f4d1c (23,046 in chips)
Seat 4: f113568e (9,075 in chips)
Seat 5: Hero (8,515 in chips)
Seat 6: e03b1647 (24,502 in chips)
Seat 7: 56b0137c (10,177 in chips)
Seat 8: cb195c66 (39,358 in chips)
e03b1647: posts the ante 45
511f4d1c: posts the ante 45
f113568e: posts the ante 45
db2c203e: posts the ante 45
56b0137c: posts the ante 45
Hero: posts the ante 45
cb195c66: posts the ante 45
4b92a21c: posts the ante 45
4b92a21c: posts small blind 175
db2c203e: posts big blind 350
*** HOLE CARDS ***
Dealt to 4b92a21c 
Dealt to db2c203e 
Dealt to 511f4d1c 
Dealt to f113568e 
Dealt to Hero [5h 7s]
Dealt to e03b1647 
Dealt to 56b0137c 
Dealt to cb195c66 
511f4d1c: folds
f113568e: folds
Hero: folds
e03b1647: folds
56b0137c: raises 350 to 700
cb195c66: folds
4b92a21c: folds
db2c203e: raises 27,682 to 28,382 and is all-in
56b0137c: calls 9,432 and is all-in
Uncalled bet (18,250) returned to db2c203e
db2c203e: shows [2d Ac]
56b0137c: shows [Ks Qs]
*** FLOP *** [7h 8c 7c]
*** TURN *** [7h 8c 7c] [6h]
*** RIVER *** [7h 8c 7c 6h] [Kc]
*** SHOWDOWN ***
56b0137c collected 20,799 from pot
*** SUMMARY ***
Total pot 20,799 | Rake 0 | Jackpot 0 | Bingo 0 | Fortune 0 | Tax 0
Board [7h 8c 7c 6h Kc]
Seat 1: 4b92a21c (small blind) folded before Flop
Seat 2: db2c203e (big blind) showed [2d Ac] and lost with a pair of Sevens
Seat 3: 511f4d1c folded before Flop
Seat 4: f113568e folded before Flop
Seat 5: Hero folded before Flop
Seat 6: e03b1647 folded before Flop
Seat 7: 56b0137c showed [Ks Qs] and won (20,799) with two pair, Kings and Sevens
Seat 8: cb195c66 (button) folded before Flop


Poker Hand #TM5543748673: Tournament #258198994, $25 GGMasters Bounty Warm-Up Special Hold'em No Limit - Level11(175/350) - 2026/02/04 00:48:48
Table '380' 8-max Seat #7 is the button
Seat 1: 4b92a21c (11,870 in chips)
Seat 2: db2c203e (27,587 in chips)
Seat 3: 511f4d1c (23,091 in chips)
Seat 4: f113568e (9,120 in chips)
Seat 5: Hero (8,560 in chips)
Seat 6: e03b1647 (24,547 in chips)
Seat 7: 56b0137c (10,222 in chips)
Seat 8: cb195c66 (39,578 in chips)
e03b1647: posts the ante 45
511f4d1c: posts the ante 45
f113568e: posts the ante 45
db2c203e: posts the ante 45
56b0137c: posts the ante 45
Hero: posts the ante 45
4b92a21c: posts the ante 45
cb195c66: posts the ante 45
cb195c66: posts small blind 175
4b92a21c: posts big blind 350
*** HOLE CARDS ***
Dealt to 4b92a21c 
Dealt to db2c203e 
Dealt to 511f4d1c 
Dealt to f113568e 
Dealt to Hero [7s 8d]
Dealt to e03b1647 
Dealt to 56b0137c 
Dealt to cb195c66 
db2c203e: raises 350 to 700
511f4d1c: folds
f113568e: folds
Hero: folds
e03b1647: folds
56b0137c: folds
cb195c66: folds
4b92a21c: folds
Uncalled bet (350) returned to db2c203e
*** SHOWDOWN ***
db2c203e collected 1,235 from pot
*** SUMMARY ***
Total pot 1,235 | Rake 0 | Jackpot 0 | Bingo 0 | Fortune 0 | Tax 0
Seat 1: 4b92a21c (big blind) folded before Flop
Seat 2: db2c203e collected (1,235)
Seat 3: 511f4d1c folded before Flop
Seat 4: f113568e folded before Flop
Seat 5: Hero folded before Flop
Seat 6: e03b1647 folded before Flop
Seat 7: 56b0137c (button) folded before Flop
Seat 8: cb195c66 (small blind) folded before Flop


Poker Hand #TM5543748614: Tournament #258198994, $25 GGMasters Bounty Warm-Up Special Hold'em No Limit - Level11(175/350) - 2026/02/04 00:47:54
Table '380' 8-max Seat #6 is the button
Seat 1: 4b92a21c (11,915 in chips)
Seat 2: db2c203e (27,632 in chips)
Seat 3: 511f4d1c (23,136 in chips)
Seat 4: f113568e (7,930 in chips)
Seat 5: Hero (8,605 in chips)
Seat 6: e03b1647 (24,592 in chips)
Seat 7: 56b0137c (10,442 in chips)
Seat 8: cb195c66 (40,323 in chips)
e03b1647: posts the ante 45
511f4d1c: posts the ante 45
f113568e: posts the ante 45
db2c203e: posts the ante 45
56b0137c: posts the ante 45
Hero: posts the ante 45
4b92a21c: posts the ante 45
cb195c66: posts the ante 45
56b0137c: posts small blind 175
cb195c66: posts big blind 350
*** HOLE CARDS ***
Dealt to 4b92a21c 
Dealt to db2c203e 
Dealt to 511f4d1c 
Dealt to f113568e 
Dealt to Hero [6s 5s]
Dealt to e03b1647 
Dealt to 56b0137c 
Dealt to cb195c66 
4b92a21c: folds
db2c203e: folds
511f4d1c: folds
f113568e: raises 350 to 700
Hero: folds
e03b1647: folds
56b0137c: folds
cb195c66: calls 350
*** FLOP *** [7d Jd 6c]
cb195c66: checks
f113568e: bets 639
cb195c66: folds
Uncalled bet (639) returned to f113568e
*** SHOWDOWN ***
f113568e collected 1,935 from pot
*** SUMMARY ***
Total pot 1,935 | Rake 0 | Jackpot 0 | Bingo 0 | Fortune 0 | Tax 0
Board [7d Jd 6c]
Seat 1: 4b92a21c folded before Flop
Seat 2: db2c203e folded before Flop
Seat 3: 511f4d1c folded before Flop
Seat 4: f113568e won (1,935)
Seat 5: Hero folded before Flop
Seat 6: e03b1647 (button) folded before Flop
Seat 7: 56b0137c (small blind) folded before Flop
Seat 8: cb195c66 (big blind) folded on the Flop


Poker Hand #TM5543748561: Tournament #258198994, $25 GGMasters Bounty Warm-Up Special Hold'em No Limit - Level10(150/300) - 2026/02/04 00:47:06
Table '380' 8-max Seat #5 is the button
Seat 1: 4b92a21c (11,950 in chips)
Seat 2: db2c203e (27,667 in chips)
Seat 3: 511f4d1c (23,171 in chips)
Seat 4: f113568e (8,865 in chips)
Seat 5: Hero (8,640 in chips)
Seat 6: e03b1647 (24,777 in chips)
Seat 7: 56b0137c (11,377 in chips)
Seat 8: cb195c66 (38,128 in chips)
511f4d1c: posts the ante 35
e03b1647: posts the ante 35
f113568e: posts the ante 35
db2c203e: posts the ante 35
56b0137c: posts the ante 35
Hero: posts the ante 35
4b92a21c: posts the ante 35
cb195c66: posts the ante 35
e03b1647: posts small blind 150
56b0137c: posts big blind 300
*** HOLE CARDS ***
Dealt to 4b92a21c 
Dealt to db2c203e 
Dealt to 511f4d1c 
Dealt to f113568e 
Dealt to Hero [5c 3h]
Dealt to e03b1647 
Dealt to 56b0137c 
Dealt to cb195c66 
cb195c66: raises 600 to 900
4b92a21c: folds
db2c203e: folds
511f4d1c: folds
f113568e: calls 900
Hero: folds
e03b1647: folds
56b0137c: calls 600
*** FLOP *** [3s 2c 2h]
56b0137c: checks
cb195c66: bets 1,800
f113568e: folds
56b0137c: folds
Uncalled bet (1,800) returned to cb195c66
*** SHOWDOWN ***
cb195c66 collected 3,130 from pot
*** SUMMARY ***
Total pot 3,130 | Rake 0 | Jackpot 0 | Bingo 0 | Fortune 0 | Tax 0
Board [3s 2c 2h]
Seat 1: 4b92a21c folded before Flop
Seat 2: db2c203e folded before Flop
Seat 3: 511f4d1c folded before Flop
Seat 4: f113568e folded on the Flop
Seat 5: Hero (button) folded before Flop
Seat 6: e03b1647 (small blind) folded before Flop
Seat 7: 56b0137c (big blind) folded on the Flop
Seat 8: cb195c66 won (3,130)


Poker Hand #TM5543748487: Tournament #258198994, $25 GGMasters Bounty Warm-Up Special Hold'em No Limit - Level10(150/300) - 2026/02/04 00:45:59
Table '380' 8-max Seat #4 is the button
Seat 1: 4b92a21c (11,985 in chips)
Seat 2: db2c203e (25,632 in chips)
Seat 3: 511f4d1c (23,206 in chips)
Seat 4: f113568e (8,900 in chips)
Seat 5: Hero (10,165 in chips)
Seat 6: e03b1647 (25,112 in chips)
Seat 7: 56b0137c (11,412 in chips)
Seat 8: cb195c66 (38,163 in chips)
511f4d1c: posts the ante 35
e03b1647: posts the ante 35
f113568e: posts the ante 35
db2c203e: posts the ante 35
56b0137c: posts the ante 35
Hero: posts the ante 35
4b92a21c: posts the ante 35
cb195c66: posts the ante 35
Hero: posts small blind 150
e03b1647: posts big blind 300
*** HOLE CARDS ***
Dealt to 4b92a21c 
Dealt to db2c203e 
Dealt to 511f4d1c 
Dealt to f113568e 
Dealt to Hero [Ac 2c]
Dealt to e03b1647 
Dealt to 56b0137c 
Dealt to cb195c66 
56b0137c: folds
cb195c66: folds
4b92a21c: folds
db2c203e: raises 300 to 600
511f4d1c: folds
f113568e: folds
Hero: calls 450
e03b1647: folds
*** FLOP *** [2h 3h Kc]
Hero: checks
db2c203e: bets 890
Hero: calls 890
*** TURN *** [2h 3h Kc] [4h]
Hero: checks
db2c203e: bets 2,350
Hero: folds
Uncalled bet (2,350) returned to db2c203e
*** SHOWDOWN ***
db2c203e collected 3,560 from pot
*** SUMMARY ***
Total pot 3,560 | Rake 0 | Jackpot 0 | Bingo 0 | Fortune 0 | Tax 0
Board [2h 3h Kc 4h]
Seat 1: 4b92a21c folded before Flop
Seat 2: db2c203e won (3,560)
Seat 3: 511f4d1c folded before Flop
Seat 4: f113568e (button) folded before Flop
Seat 5: Hero (small blind) folded on the Turn
Seat 6: e03b1647 (big blind) folded before Flop
Seat 7: 56b0137c folded before Flop
Seat 8: cb195c66 folded before Flop


Poker Hand #TM5543748406: Tournament #258198994, $25 GGMasters Bounty Warm-Up Special Hold'em No Limit - Level10(150/300) - 2026/02/04 00:44:46
Table '380' 8-max Seat #3 is the button
Seat 1: 4b92a21c (12,020 in chips)
Seat 2: db2c203e (25,667 in chips)
Seat 3: 511f4d1c (23,841 in chips)
Seat 4: f113568e (9,085 in chips)
Seat 5: Hero (10,800 in chips)
Seat 6: e03b1647 (25,147 in chips)
Seat 7: 56b0137c (12,047 in chips)
Seat 8: cb195c66 (35,968 in chips)
511f4d1c: posts the ante 35
e03b1647: posts the ante 35
f113568e: posts the ante 35
db2c203e: posts the ante 35
56b0137c: posts the ante 35
Hero: posts the ante 35
4b92a21c: posts the ante 35
cb195c66: posts the ante 35
f113568e: posts small blind 150
Hero: posts big blind 300
*** HOLE CARDS ***
Dealt to 4b92a21c 
Dealt to db2c203e 
Dealt to 511f4d1c 
Dealt to f113568e 
Dealt to Hero [Ad Jh]
Dealt to e03b1647 
Dealt to 56b0137c 
Dealt to cb195c66 
e03b1647: folds
56b0137c: raises 300 to 600
cb195c66: calls 600
4b92a21c: folds
db2c203e: folds
511f4d1c: calls 600
f113568e: folds
Hero: calls 300
*** FLOP *** [Ks 7s 5s]
Hero: checks
56b0137c: checks
cb195c66: bets 1,800
511f4d1c: folds
Hero: folds
56b0137c: folds
Uncalled bet (1,800) returned to cb195c66
*** SHOWDOWN ***
cb195c66 collected 2,830 from pot
*** SUMMARY ***
Total pot 2,830 | Rake 0 | Jackpot 0 | Bingo 0 | Fortune 0 | Tax 0
Board [Ks 7s 5s]
Seat 1: 4b92a21c folded before Flop
Seat 2: db2c203e folded before Flop
Seat 3: 511f4d1c (button) folded on the Flop
Seat 4: f113568e (small blind) folded before Flop
Seat 5: Hero (big blind) folded on the Flop
Seat 6: e03b1647 folded before Flop
Seat 7: 56b0137c folded on the Flop
Seat 8: cb195c66 won (2,830)


Poker Hand #TM5543748348: Tournament #258198994, $25 GGMasters Bounty Warm-Up Special Hold'em No Limit - Level10(150/300) - 2026/02/04 00:43:57
Table '380' 8-max Seat #2 is the button
Seat 1: 4b92a21c (12,055 in chips)
Seat 2: db2c203e (23,857 in chips)
Seat 3: 511f4d1c (24,026 in chips)
Seat 4: f113568e (10,535 in chips)
Seat 5: Hero (10,835 in chips)
Seat 6: e03b1647 (25,182 in chips)
Seat 7: 56b0137c (12,082 in chips)
Seat 8: cb195c66 (36,003 in chips)
e03b1647: posts the ante 35
511f4d1c: posts the ante 35
f113568e: posts the ante 35
db2c203e: posts the ante 35
56b0137c: posts the ante 35
Hero: posts the ante 35
4b92a21c: posts the ante 35
cb195c66: posts the ante 35
511f4d1c: posts small blind 150
f113568e: posts big blind 300
*** HOLE CARDS ***
Dealt to 4b92a21c 
Dealt to db2c203e 
Dealt to 511f4d1c 
Dealt to f113568e 
Dealt to Hero [6d Th]
Dealt to e03b1647 
Dealt to 56b0137c 
Dealt to cb195c66 
Hero: folds
e03b1647: folds
56b0137c: folds
cb195c66: folds
4b92a21c: folds
db2c203e: raises 300 to 600
511f4d1c: folds
f113568e: calls 300
*** FLOP *** [Qd Kd 7h]
f113568e: checks
db2c203e: bets 815
f113568e: calls 815
*** TURN *** [Qd Kd 7h] [Ac]
f113568e: checks
db2c203e: bets 2,445
f113568e: folds
Uncalled bet (2,445) returned to db2c203e
*** SHOWDOWN ***
db2c203e collected 3,260 from pot
*** SUMMARY ***
Total pot 3,260 | Rake 0 | Jackpot 0 | Bingo 0 | Fortune 0 | Tax 0
Board [Qd Kd 7h Ac]
Seat 1: 4b92a21c folded before Flop
Seat 2: db2c203e (button) won (3,260)
Seat 3: 511f4d1c (small blind) folded before Flop
Seat 4: f113568e (big blind) folded on the Turn
Seat 5: Hero folded before Flop
Seat 6: e03b1647 folded before Flop
Seat 7: 56b0137c folded before Flop
Seat 8: cb195c66 folded before Flop


Poker Hand #TM5543748254: Tournament #258198994, $25 GGMasters Bounty Warm-Up Special Hold'em No Limit - Level10(150/300) - 2026/02/04 00:42:31
Table '380' 8-max Seat #1 is the button
Seat 1: 4b92a21c (12,090 in chips)
Seat 2: db2c203e (22,112 in chips)
Seat 3: 511f4d1c (25,561 in chips)
Seat 4: f113568e (10,570 in chips)
Seat 5: Hero (10,870 in chips)
Seat 6: e03b1647 (25,217 in chips)
Seat 7: 56b0137c (12,117 in chips)
Seat 8: cb195c66 (36,038 in chips)
e03b1647: posts the ante 35
511f4d1c: posts the ante 35
f113568e: posts the ante 35
db2c203e: posts the ante 35
56b0137c: posts the ante 35
Hero: posts the ante 35
4b92a21c: posts the ante 35
cb195c66: posts the ante 35
db2c203e: posts small blind 150
511f4d1c: posts big blind 300
*** HOLE CARDS ***
Dealt to 4b92a21c 
Dealt to db2c203e 
Dealt to 511f4d1c 
Dealt to f113568e 
Dealt to Hero [5c Jd]
Dealt to e03b1647 
Dealt to 56b0137c 
Dealt to cb195c66 
f113568e: folds
Hero: folds
e03b1647: folds
56b0137c: folds
cb195c66: folds
4b92a21c: folds
db2c203e: calls 150
511f4d1c: checks
*** FLOP *** [8c Ad 7c]
db2c203e: bets 300
511f4d1c: calls 300
*** TURN *** [8c Ad 7c] [9d]
db2c203e: bets 900
511f4d1c: calls 900
*** RIVER *** [8c Ad 7c 9d] [6d]
db2c203e: bets 3,600
511f4d1c: folds
Uncalled bet (3,600) returned to db2c203e
*** SHOWDOWN ***
db2c203e collected 3,280 from pot
*** SUMMARY ***
Total pot 3,280 | Rake 0 | Jackpot 0 | Bingo 0 | Fortune 0 | Tax 0
Board [8c Ad 7c 9d 6d]
Seat 1: 4b92a21c (button) folded before Flop
Seat 2: db2c203e (small blind) won (3,280)
Seat 3: 511f4d1c (big blind) folded on the River
Seat 4: f113568e folded before Flop
Seat 5: Hero folded before Flop
Seat 6: e03b1647 folded before Flop
Seat 7: 56b0137c folded before Flop
Seat 8: cb195c66 folded before Flop


Poker Hand #TM5543748166: Tournament #258198994, $25 GGMasters Bounty Warm-Up Special Hold'em No Limit - Level10(150/300) - 2026/02/04 00:41:08
Table '380' 8-max Seat #8 is the button
Seat 1: 4b92a21c (9,595 in chips)
Seat 2: db2c203e (24,397 in chips)
Seat 3: 511f4d1c (25,596 in chips)
Seat 4: f113568e (10,605 in chips)
Seat 5: Hero (10,905 in chips)
Seat 6: e03b1647 (25,252 in chips)
Seat 7: 56b0137c (12,152 in chips)
Seat 8: cb195c66 (36,073 in chips)
e03b1647: posts the ante 35
511f4d1c: posts the ante 35
f113568e: posts the ante 35
db2c203e: posts the ante 35
56b0137c: posts the ante 35
Hero: posts the ante 35
cb195c66: posts the ante 35
4b92a21c: posts the ante 35
4b92a21c: posts small blind 150
db2c203e: posts big blind 300
*** HOLE CARDS ***
Dealt to 4b92a21c 
Dealt to db2c203e 
Dealt to 511f4d1c 
Dealt to f113568e 
Dealt to Hero [4s 5h]
Dealt to e03b1647 
Dealt to 56b0137c 
Dealt to cb195c66 
511f4d1c: folds
f113568e: folds
Hero: folds
e03b1647: folds
56b0137c: folds
cb195c66: folds
4b92a21c: calls 150
db2c203e: raises 600 to 900
4b92a21c: calls 600
*** FLOP *** [8d 3s 6h]
4b92a21c: checks
db2c203e: bets 1,350
4b92a21c: calls 1,350
*** TURN *** [8d 3s 6h] [5d]
4b92a21c: bets 2,400
db2c203e: folds
Uncalled bet (2,400) returned to 4b92a21c
*** SHOWDOWN ***
4b92a21c collected 4,780 from pot
*** SUMMARY ***
Total pot 4,780 | Rake 0 | Jackpot 0 | Bingo 0 | Fortune 0 | Tax 0
Board [8d 3s 6h 5d]
Seat 1: 4b92a21c (small blind) won (4,780)
Seat 2: db2c203e (big blind) folded on the Turn
Seat 3: 511f4d1c folded before Flop
Seat 4: f113568e folded before Flop
Seat 5: Hero folded before Flop
Seat 6: e03b1647 folded before Flop
Seat 7: 56b0137c folded before Flop
Seat 8: cb195c66 (button) folded before Flop


Poker Hand #TM5543748124: Tournament #258198994, $25 GGMasters Bounty Warm-Up Special Hold'em No Limit - Level10(150/300) - 2026/02/04 00:40:24
Table '380' 8-max Seat #7 is the button
Seat 1: 4b92a21c (9,930 in chips)
Seat 2: db2c203e (24,432 in chips)
Seat 3: 511f4d1c (25,631 in chips)
Seat 4: f113568e (8,673 in chips)
Seat 5: Hero (10,940 in chips)
Seat 6: e03b1647 (25,287 in chips)
Seat 7: 56b0137c (13,424 in chips)
Seat 8: cb195c66 (36,258 in chips)
e03b1647: posts the ante 35
511f4d1c: posts the ante 35
f113568e: posts the ante 35
db2c203e: posts the ante 35
56b0137c: posts the ante 35
Hero: posts the ante 35
4b92a21c: posts the ante 35
cb195c66: posts the ante 35
cb195c66: posts small blind 150
4b92a21c: posts big blind 300
*** HOLE CARDS ***
Dealt to 4b92a21c 
Dealt to db2c203e 
Dealt to 511f4d1c 
Dealt to f113568e 
Dealt to Hero [6d 8d]
Dealt to e03b1647 
Dealt to 56b0137c 
Dealt to cb195c66 
db2c203e: folds
511f4d1c: folds
f113568e: raises 300 to 600
Hero: folds
e03b1647: folds
56b0137c: calls 600
cb195c66: folds
4b92a21c: folds
*** FLOP *** [As Qd Td]
f113568e: bets 637
56b0137c: calls 637
*** TURN *** [As Qd Td] [3s]
f113568e: checks
56b0137c: checks
*** RIVER *** [As Qd Td 3s] [4d]
f113568e: checks
56b0137c: checks
f113568e: shows [Ad 9c] (a pair of Aces)
56b0137c: shows [Kc Th] (a pair of Tens)
*** SHOWDOWN ***
f113568e collected 3,204 from pot
*** SUMMARY ***
Total pot 3,204 | Rake 0 | Jackpot 0 | Bingo 0 | Fortune 0 | Tax 0
Board [As Qd Td 3s 4d]
Seat 1: 4b92a21c (big blind) folded before Flop
Seat 2: db2c203e folded before Flop
Seat 3: 511f4d1c folded before Flop
Seat 4: f113568e showed [Ad 9c] and won (3,204) with a pair of Aces
Seat 5: Hero folded before Flop
Seat 6: e03b1647 folded before Flop
Seat 7: 56b0137c (button) showed [Kc Th] and lost with a pair of Tens
Seat 8: cb195c66 (small blind) folded before Flop


Poker Hand #TM5543748072: Tournament #258198994, $25 GGMasters Bounty Warm-Up Special Hold'em No Limit - Level10(150/300) - 2026/02/04 00:39:43
Table '380' 8-max Seat #6 is the button
Seat 1: 4b92a21c (9,965 in chips)
Seat 2: db2c203e (23,287 in chips)
Seat 3: 511f4d1c (25,666 in chips)
Seat 4: f113568e (8,708 in chips)
Seat 5: Hero (10,975 in chips)
Seat 6: e03b1647 (25,322 in chips)
Seat 7: 56b0137c (14,059 in chips)
Seat 8: cb195c66 (36,593 in chips)
e03b1647: posts the ante 35
511f4d1c: posts the ante 35
f113568e: posts the ante 35
db2c203e: posts the ante 35
56b0137c: posts the ante 35
Hero: posts the ante 35
4b92a21c: posts the ante 35
cb195c66: posts the ante 35
56b0137c: posts small blind 150
cb195c66: posts big blind 300
*** HOLE CARDS ***
Dealt to 4b92a21c 
Dealt to db2c203e 
Dealt to 511f4d1c 
Dealt to f113568e 
Dealt to Hero [6c 7h]
Dealt to e03b1647 
Dealt to 56b0137c 
Dealt to cb195c66 
4b92a21c: folds
db2c203e: raises 300 to 600
511f4d1c: folds
f113568e: folds
Hero: folds
e03b1647: folds
56b0137c: calls 450
cb195c66: folds
*** FLOP *** [Js Qd Qs]
56b0137c: checks
db2c203e: checks
*** TURN *** [Js Qd Qs] [Jd]
56b0137c: checks
db2c203e: bets 588
56b0137c: folds
Uncalled bet (588) returned to db2c203e
*** SHOWDOWN ***
db2c203e collected 1,780 from pot
*** SUMMARY ***
Total pot 1,780 | Rake 0 | Jackpot 0 | Bingo 0 | Fortune 0 | Tax 0
Board [Js Qd Qs Jd]
Seat 1: 4b92a21c folded before Flop
Seat 2: db2c203e won (1,780)
Seat 3: 511f4d1c folded before Flop
Seat 4: f113568e folded before Flop
Seat 5: Hero folded before Flop
Seat 6: e03b1647 (button) folded before Flop
Seat 7: 56b0137c (small blind) folded on the Turn
Seat 8: cb195c66 (big blind) folded before Flop


Poker Hand #TM5543748003: Tournament #258198994, $25 GGMasters Bounty Warm-Up Special Hold'em No Limit - Level10(150/300) - 2026/02/04 00:38:41
Table '380' 8-max Seat #5 is the button
Seat 1: 4b92a21c (10,000 in chips)
Seat 2: db2c203e (23,322 in chips)
Seat 3: 511f4d1c (22,421 in chips)
Seat 4: f113568e (8,743 in chips)
Seat 5: Hero (11,010 in chips)
Seat 6: e03b1647 (25,507 in chips)
Seat 7: 56b0137c (14,394 in chips)
Seat 8: cb195c66 (39,178 in chips)
511f4d1c: posts the ante 35
e03b1647: posts the ante 35
f113568e: posts the ante 35
db2c203e: posts the ante 35
56b0137c: posts the ante 35
Hero: posts the ante 35
4b92a21c: posts the ante 35
cb195c66: posts the ante 35
e03b1647: posts small blind 150
56b0137c: posts big blind 300
*** HOLE CARDS ***
Dealt to 4b92a21c 
Dealt to db2c203e 
Dealt to 511f4d1c 
Dealt to f113568e 
Dealt to Hero [6d 7c]
Dealt to e03b1647 
Dealt to 56b0137c 
Dealt to cb195c66 
cb195c66: raises 600 to 900
4b92a21c: folds
db2c203e: folds
511f4d1c: raises 1,650 to 2,550
f113568e: folds
Hero: folds
e03b1647: folds
56b0137c: folds
cb195c66: calls 1,650
*** FLOP *** [Qs 6c 5h]
cb195c66: checks
511f4d1c: bets 1,458
cb195c66: folds
Uncalled bet (1,458) returned to 511f4d1c
*** SHOWDOWN ***
511f4d1c collected 5,830 from pot
*** SUMMARY ***
Total pot 5,830 | Rake 0 | Jackpot 0 | Bingo 0 | Fortune 0 | Tax 0
Board [Qs 6c 5h]
Seat 1: 4b92a21c folded before Flop
Seat 2: db2c203e folded before Flop
Seat 3: 511f4d1c won (5,830)
Seat 4: f113568e folded before Flop
Seat 5: Hero (button) folded before Flop
Seat 6: e03b1647 (small blind) folded before Flop
Seat 7: 56b0137c (big blind) folded before Flop
Seat 8: cb195c66 folded on the Flop


Poker Hand #TM5543747918: Tournament #258198994, $25 GGMasters Bounty Warm-Up Special Hold'em No Limit - Level10(150/300) - 2026/02/04 00:37:25
Table '380' 8-max Seat #4 is the button
Seat 2: db2c203e (23,357 in chips)
Seat 3: 511f4d1c (22,456 in chips)
Seat 4: f113568e (8,778 in chips)
Seat 5: Hero (11,195 in chips)
Seat 6: e03b1647 (23,797 in chips)
Seat 7: 56b0137c (15,779 in chips)
Seat 8: cb195c66 (39,213 in chips)
511f4d1c: posts the ante 35
e03b1647: posts the ante 35
f113568e: posts the ante 35
db2c203e: posts the ante 35
56b0137c: posts the ante 35
Hero: posts the ante 35
cb195c66: posts the ante 35
Hero: posts small blind 150
e03b1647: posts big blind 300
*** HOLE CARDS ***
Dealt to db2c203e 
Dealt to 511f4d1c 
Dealt to f113568e 
Dealt to Hero [8d As]
Dealt to e03b1647 
Dealt to 56b0137c 
Dealt to cb195c66 
56b0137c: raises 300 to 600
cb195c66: folds
db2c203e: folds
511f4d1c: folds
f113568e: folds
Hero: folds
e03b1647: calls 300
*** FLOP *** [5c Jd 4d]
e03b1647: checks
56b0137c: bets 750
e03b1647: calls 750
*** TURN *** [5c Jd 4d] [6d]
e03b1647: checks
56b0137c: checks
*** RIVER *** [5c Jd 4d 6d] [8c]
e03b1647: bets 600
56b0137c: folds
Uncalled bet (600) returned to e03b1647
*** SHOWDOWN ***
e03b1647 collected 3,095 from pot
*** SUMMARY ***
Total pot 3,095 | Rake 0 | Jackpot 0 | Bingo 0 | Fortune 0 | Tax 0
Board [5c Jd 4d 6d 8c]
Seat 2: db2c203e folded before Flop
Seat 3: 511f4d1c folded before Flop
Seat 4: f113568e (button) folded before Flop
Seat 5: Hero (small blind) folded before Flop
Seat 6: e03b1647 (big blind) won (3,095)
Seat 7: 56b0137c folded on the River
Seat 8: cb195c66 folded before Flop


Poker Hand #TM5543747869: Tournament #258198994, $25 GGMasters Bounty Warm-Up Special Hold'em No Limit - Level9(125/250) - 2026/02/04 00:36:39
Table '380' 8-max Seat #3 is the button
Seat 2: db2c203e (23,887 in chips)
Seat 3: 511f4d1c (22,486 in chips)
Seat 4: f113568e (7,848 in chips)
Seat 5: Hero (11,475 in chips)
Seat 6: e03b1647 (23,827 in chips)
Seat 7: 56b0137c (15,809 in chips)
Seat 8: cb195c66 (39,243 in chips)
511f4d1c: posts the ante 30
e03b1647: posts the ante 30
f113568e: posts the ante 30
db2c203e: posts the ante 30
56b0137c: posts the ante 30
Hero: posts the ante 30
cb195c66: posts the ante 30
f113568e: posts small blind 125
Hero: posts big blind 250
*** HOLE CARDS ***
Dealt to db2c203e 
Dealt to 511f4d1c 
Dealt to f113568e 
Dealt to Hero [Qh Jd]
Dealt to e03b1647 
Dealt to 56b0137c 
Dealt to cb195c66 
e03b1647: folds
56b0137c: folds
cb195c66: folds
db2c203e: raises 250 to 500
511f4d1c: folds
f113568e: raises 7,318 to 7,818 and is all-in
Hero: folds
db2c203e: folds
Uncalled bet (7,318) returned to f113568e
*** SHOWDOWN ***
f113568e collected 1,460 from pot
*** SUMMARY ***
Total pot 1,460 | Rake 0 | Jackpot 0 | Bingo 0 | Fortune 0 | Tax 0
Seat 2: db2c203e folded before Flop
Seat 3: 511f4d1c (button) folded before Flop
Seat 4: f113568e (small blind) collected (1,460)
Seat 5: Hero (big blind) folded before Flop
Seat 6: e03b1647 folded before Flop
Seat 7: 56b0137c folded before Flop
Seat 8: cb195c66 folded before Flop


Poker Hand #TM5543747806: Tournament #258198994, $25 GGMasters Bounty Warm-Up Special Hold'em No Limit - Level9(125/250) - 2026/02/04 00:35:57
Table '380' 8-max Seat #2 is the button
Seat 2: db2c203e (23,917 in chips)
Seat 3: 511f4d1c (22,641 in chips)
Seat 4: f113568e (8,428 in chips)
Seat 5: Hero (10,620 in chips)
Seat 6: e03b1647 (23,857 in chips)
Seat 7: 56b0137c (15,839 in chips)
Seat 8: cb195c66 (39,273 in chips)
e03b1647: posts the ante 30
511f4d1c: posts the ante 30
f113568e: posts the ante 30
db2c203e: posts the ante 30
56b0137c: posts the ante 30
Hero: posts the ante 30
cb195c66: posts the ante 30
511f4d1c: posts small blind 125
f113568e: posts big blind 250
*** HOLE CARDS ***
Dealt to db2c203e 
Dealt to 511f4d1c 
Dealt to f113568e 
Dealt to Hero [Ad Js]
Dealt to e03b1647 
Dealt to 56b0137c 
Dealt to cb195c66 
Hero: raises 300 to 550
e03b1647: folds
56b0137c: folds
cb195c66: folds
db2c203e: folds
511f4d1c: folds
f113568e: calls 300
*** FLOP *** [Jd 3h 6h]
f113568e: checks
Hero: bets 718
f113568e: folds
Uncalled bet (718) returned to Hero
*** SHOWDOWN ***
Hero collected 1,435 from pot
*** SUMMARY ***
Total pot 1,435 | Rake 0 | Jackpot 0 | Bingo 0 | Fortune 0 | Tax 0
Board [Jd 3h 6h]
Seat 2: db2c203e (button) folded before Flop
Seat 3: 511f4d1c (small blind) folded before Flop
Seat 4: f113568e (big blind) folded on the Flop
Seat 5: Hero won (1,435)
Seat 6: e03b1647 folded before Flop
Seat 7: 56b0137c folded before Flop
Seat 8: cb195c66 folded before Flop


Poker Hand #TM5543747741: Tournament #258198994, $25 GGMasters Bounty Warm-Up Special Hold'em No Limit - Level9(125/250) - 2026/02/04 00:34:54
Table '380' 8-max Seat #8 is the button
Seat 2: db2c203e (24,447 in chips)
Seat 3: 511f4d1c (22,921 in chips)
Seat 4: f113568e (7,498 in chips)
Seat 5: Hero (10,650 in chips)
Seat 6: e03b1647 (23,887 in chips)
Seat 7: 56b0137c (15,869 in chips)
Seat 8: cb195c66 (39,303 in chips)
e03b1647: posts the ante 30
511f4d1c: posts the ante 30
f113568e: posts the ante 30
db2c203e: posts the ante 30
56b0137c: posts the ante 30
Hero: posts the ante 30
cb195c66: posts the ante 30
db2c203e: posts small blind 125
511f4d1c: posts big blind 250
*** HOLE CARDS ***
Dealt to db2c203e 
Dealt to 511f4d1c 
Dealt to f113568e 
Dealt to Hero [7h 8d]
Dealt to e03b1647 
Dealt to 56b0137c 
Dealt to cb195c66 
f113568e: raises 250 to 500
Hero: folds
e03b1647: folds
56b0137c: folds
cb195c66: folds
db2c203e: calls 375
511f4d1c: folds
*** FLOP *** [Ac Td Ah]
db2c203e: checks
f113568e: bets 482
db2c203e: folds
Uncalled bet (482) returned to f113568e
*** SHOWDOWN ***
f113568e collected 1,460 from pot
*** SUMMARY ***
Total pot 1,460 | Rake 0 | Jackpot 0 | Bingo 0 | Fortune 0 | Tax 0
Board [Ac Td Ah]
Seat 2: db2c203e (small blind) folded on the Flop
Seat 3: 511f4d1c (big blind) folded before Flop
Seat 4: f113568e won (1,460)
Seat 5: Hero folded before Flop
Seat 6: e03b1647 folded before Flop
Seat 7: 56b0137c folded before Flop
Seat 8: cb195c66 (button) folded before Flop


Poker Hand #TM5543747707: Tournament #258198994, $25 GGMasters Bounty Warm-Up Special Hold'em No Limit - Level9(125/250) - 2026/02/04 00:34:23
Table '380' 8-max Seat #7 is the button
Seat 2: db2c203e (24,727 in chips)
Seat 3: 511f4d1c (23,451 in chips)
Seat 4: f113568e (7,528 in chips)
Seat 5: Hero (11,180 in chips)
Seat 6: e03b1647 (23,917 in chips)
Seat 7: 56b0137c (15,899 in chips)
Seat 8: cb195c66 (37,873 in chips)
e03b1647: posts the ante 30
511f4d1c: posts the ante 30
f113568e: posts the ante 30
db2c203e: posts the ante 30
56b0137c: posts the ante 30
Hero: posts the ante 30
cb195c66: posts the ante 30
cb195c66: posts small blind 125
db2c203e: posts big blind 250
*** HOLE CARDS ***
Dealt to db2c203e 
Dealt to 511f4d1c 
Dealt to f113568e 
Dealt to Hero [Ah 2h]
Dealt to e03b1647 
Dealt to 56b0137c 
Dealt to cb195c66 
511f4d1c: raises 250 to 500
f113568e: folds
Hero: calls 500
e03b1647: folds
56b0137c: folds
cb195c66: raises 3,000 to 3,500
db2c203e: folds
511f4d1c: folds
Hero: folds
Uncalled bet (3,000) returned to cb195c66
*** SHOWDOWN ***
cb195c66 collected 1,960 from pot
*** SUMMARY ***
Total pot 1,960 | Rake 0 | Jackpot 0 | Bingo 0 | Fortune 0 | Tax 0
Seat 2: db2c203e (big blind) folded before Flop
Seat 3: 511f4d1c folded before Flop
Seat 4: f113568e folded before Flop
Seat 5: Hero folded before Flop
Seat 6: e03b1647 folded before Flop
Seat 7: 56b0137c (button) folded before Flop
Seat 8: cb195c66 (small blind) collected (1,960)


Poker Hand #TM5543747682: Tournament #258198994, $25 GGMasters Bounty Warm-Up Special Hold'em No Limit - Level9(125/250) - 2026/02/04 00:34:00
Table '380' 8-max Seat #6 is the button
Seat 2: db2c203e (24,757 in chips)
Seat 3: 511f4d1c (23,481 in chips)
Seat 4: f113568e (7,558 in chips)
Seat 5: Hero (10,625 in chips)
Seat 6: e03b1647 (23,947 in chips)
Seat 7: 56b0137c (16,054 in chips)
Seat 8: cb195c66 (38,153 in chips)
e03b1647: posts the ante 30
511f4d1c: posts the ante 30
f113568e: posts the ante 30
db2c203e: posts the ante 30
56b0137c: posts the ante 30
Hero: posts the ante 30
cb195c66: posts the ante 30
56b0137c: posts small blind 125
cb195c66: posts big blind 250
*** HOLE CARDS ***
Dealt to db2c203e 
Dealt to 511f4d1c 
Dealt to f113568e 
Dealt to Hero [9d Ad]
Dealt to e03b1647 
Dealt to 56b0137c 
Dealt to cb195c66 
db2c203e: folds
511f4d1c: folds
f113568e: folds
Hero: raises 300 to 550
e03b1647: folds
56b0137c: folds
cb195c66: folds
Uncalled bet (300) returned to Hero
*** SHOWDOWN ***
Hero collected 835 from pot
*** SUMMARY ***
Total pot 835 | Rake 0 | Jackpot 0 | Bingo 0 | Fortune 0 | Tax 0
Seat 2: db2c203e folded before Flop
Seat 3: 511f4d1c folded before Flop
Seat 4: f113568e folded before Flop
Seat 5: Hero collected (835)
Seat 6: e03b1647 (button) folded before Flop
Seat 7: 56b0137c (small blind) folded before Flop
Seat 8: cb195c66 (big blind) folded before Flop


Poker Hand #TM5543747620: Tournament #258198994, $25 GGMasters Bounty Warm-Up Special Hold'em No Limit - Level9(125/250) - 2026/02/04 00:33:06
Table '380' 8-max Seat #5 is the button
Seat 1: 7ec89b34 (2,573 in chips)
Seat 2: db2c203e (24,787 in chips)
Seat 3: 511f4d1c (23,511 in chips)
Seat 4: f113568e (7,588 in chips)
Seat 5: Hero (10,655 in chips)
Seat 6: e03b1647 (24,102 in chips)
Seat 7: 56b0137c (16,334 in chips)
Seat 8: cb195c66 (35,025 in chips)
511f4d1c: posts the ante 30
e03b1647: posts the ante 30
f113568e: posts the ante 30
db2c203e: posts the ante 30
7ec89b34: posts the ante 30
56b0137c: posts the ante 30
Hero: posts the ante 30
cb195c66: posts the ante 30
e03b1647: posts small blind 125
56b0137c: posts big blind 250
*** HOLE CARDS ***
Dealt to 7ec89b34 
Dealt to db2c203e 
Dealt to 511f4d1c 
Dealt to f113568e 
Dealt to Hero [Qc Td]
Dealt to e03b1647 
Dealt to 56b0137c 
Dealt to cb195c66 
cb195c66: calls 250
7ec89b34: raises 2,293 to 2,543 and is all-in
db2c203e: folds
511f4d1c: folds
f113568e: folds
Hero: folds
e03b1647: folds
56b0137c: folds
cb195c66: calls 2,293
7ec89b34: shows [7d 7h]
cb195c66: shows [Ad 2d]
*** FLOP *** [Th 9s Tc]
*** TURN *** [Th 9s Tc] [9c]
*** RIVER *** [Th 9s Tc 9c] [4h]
*** SHOWDOWN ***
cb195c66 collected 5,701 from pot
*** SUMMARY ***
Total pot 5,701 | Rake 0 | Jackpot 0 | Bingo 0 | Fortune 0 | Tax 0
Board [Th 9s Tc 9c 4h]
Seat 1: 7ec89b34 showed [7d 7h] and lost with two pair, Tens and Nines
Seat 2: db2c203e folded before Flop
Seat 3: 511f4d1c folded before Flop
Seat 4: f113568e folded before Flop
Seat 5: Hero (button) folded before Flop
Seat 6: e03b1647 (small blind) folded before Flop
Seat 7: 56b0137c (big blind) folded before Flop
Seat 8: cb195c66 showed [Ad 2d] and won (5,701) with two pair, Tens and Nines


Poker Hand #TM5543747540: Tournament #258198994, $25 GGMasters Bounty Warm-Up Special Hold'em No Limit - Level9(125/250) - 2026/02/04 00:32:03
Table '380' 8-max Seat #4 is the button
Seat 1: 7ec89b34 (2,603 in chips)
Seat 2: db2c203e (24,817 in chips)
Seat 3: 511f4d1c (23,541 in chips)
Seat 4: f113568e (7,618 in chips)
Seat 5: Hero (9,195 in chips)
Seat 6: e03b1647 (24,382 in chips)
Seat 7: 56b0137c (17,364 in chips)
Seat 8: cb195c66 (35,055 in chips)
511f4d1c: posts the ante 30
e03b1647: posts the ante 30
f113568e: posts the ante 30
db2c203e: posts the ante 30
7ec89b34: posts the ante 30
56b0137c: posts the ante 30
Hero: posts the ante 30
cb195c66: posts the ante 30
Hero: posts small blind 125
e03b1647: posts big blind 250
*** HOLE CARDS ***
Dealt to 7ec89b34 
Dealt to db2c203e 
Dealt to 511f4d1c 
Dealt to f113568e 
Dealt to Hero [Ac Td]
Dealt to e03b1647 
Dealt to 56b0137c 
Dealt to cb195c66 
56b0137c: raises 250 to 500
cb195c66: folds
7ec89b34: folds
db2c203e: folds
511f4d1c: folds
f113568e: folds
Hero: calls 375
e03b1647: folds
*** FLOP *** [6s Tc 4h]
Hero: checks
56b0137c: bets 500
Hero: raises 1,000 to 1,500
56b0137c: folds
Uncalled bet (1,000) returned to Hero
*** SHOWDOWN ***
Hero collected 2,490 from pot
*** SUMMARY ***
Total pot 2,490 | Rake 0 | Jackpot 0 | Bingo 0 | Fortune 0 | Tax 0
Board [6s Tc 4h]
Seat 1: 7ec89b34 folded before Flop
Seat 2: db2c203e folded before Flop
Seat 3: 511f4d1c folded before Flop
Seat 4: f113568e (button) folded before Flop
Seat 5: Hero (small blind) won (2,490)
Seat 6: e03b1647 (big blind) folded before Flop
Seat 7: 56b0137c folded on the Flop
Seat 8: cb195c66 folded before Flop


Poker Hand #TM5543747490: Tournament #258198994, $25 GGMasters Bounty Warm-Up Special Hold'em No Limit - Level9(125/250) - 2026/02/04 00:31:19
Table '380' 8-max Seat #3 is the button
Seat 1: 7ec89b34 (2,633 in chips)
Seat 2: db2c203e (23,232 in chips)
Seat 3: 511f4d1c (23,571 in chips)
Seat 4: f113568e (7,773 in chips)
Seat 5: Hero (9,475 in chips)
Seat 6: e03b1647 (24,412 in chips)
Seat 7: 56b0137c (17,894 in chips)
Seat 8: cb195c66 (35,585 in chips)
511f4d1c: posts the ante 30
e03b1647: posts the ante 30
f113568e: posts the ante 30
db2c203e: posts the ante 30
7ec89b34: posts the ante 30
56b0137c: posts the ante 30
Hero: posts the ante 30
cb195c66: posts the ante 30
f113568e: posts small blind 125
Hero: posts big blind 250
*** HOLE CARDS ***
Dealt to 7ec89b34 
Dealt to db2c203e 
Dealt to 511f4d1c 
Dealt to f113568e 
Dealt to Hero [6s Kc]
Dealt to e03b1647 
Dealt to 56b0137c 
Dealt to cb195c66 
e03b1647: folds
56b0137c: raises 250 to 500
cb195c66: calls 500
7ec89b34: folds
db2c203e: raises 1,750 to 2,250
511f4d1c: folds
f113568e: folds
Hero: folds
56b0137c: folds
cb195c66: folds
Uncalled bet (1,750) returned to db2c203e
*** SHOWDOWN ***
db2c203e collected 2,115 from pot
*** SUMMARY ***
Total pot 2,115 | Rake 0 | Jackpot 0 | Bingo 0 | Fortune 0 | Tax 0
Seat 1: 7ec89b34 folded before Flop
Seat 2: db2c203e collected (2,115)
Seat 3: 511f4d1c (button) folded before Flop
Seat 4: f113568e (small blind) folded before Flop
Seat 5: Hero (big blind) folded before Flop
Seat 6: e03b1647 folded before Flop
Seat 7: 56b0137c folded before Flop
Seat 8: cb195c66 folded before Flop


Poker Hand #TM5543747462: Tournament #258198994, $25 GGMasters Bounty Warm-Up Special Hold'em No Limit - Level9(125/250) - 2026/02/04 00:30:54
Table '380' 8-max Seat #2 is the button
Seat 1: 7ec89b34 (2,663 in chips)
Seat 2: db2c203e (23,262 in chips)
Seat 3: 511f4d1c (23,726 in chips)
Seat 4: f113568e (8,053 in chips)
Seat 5: Hero (9,505 in chips)
Seat 6: e03b1647 (24,442 in chips)
Seat 7: 56b0137c (17,924 in chips)
Seat 8: cb195c66 (35,000 in chips)
e03b1647: posts the ante 30
511f4d1c: posts the ante 30
f113568e: posts the ante 30
db2c203e: posts the ante 30
7ec89b34: posts the ante 30
56b0137c: posts the ante 30
Hero: posts the ante 30
cb195c66: posts the ante 30
511f4d1c: posts small blind 125
f113568e: posts big blind 250
*** HOLE CARDS ***
Dealt to 7ec89b34 
Dealt to db2c203e 
Dealt to 511f4d1c 
Dealt to f113568e 
Dealt to Hero [Kd Jh]
Dealt to e03b1647 
Dealt to 56b0137c 
Dealt to cb195c66 
Hero: folds
e03b1647: folds
56b0137c: folds
cb195c66: raises 500 to 750
7ec89b34: folds
db2c203e: folds
511f4d1c: folds
f113568e: folds
Uncalled bet (500) returned to cb195c66
*** SHOWDOWN ***
cb195c66 collected 865 from pot
*** SUMMARY ***
Total pot 865 | Rake 0 | Jackpot 0 | Bingo 0 | Fortune 0 | Tax 0
Seat 1: 7ec89b34 folded before Flop
Seat 2: db2c203e (button) folded before Flop
Seat 3: 511f4d1c (small blind) folded before Flop
Seat 4: f113568e (big blind) folded before Flop
Seat 5: Hero folded before Flop
Seat 6: e03b1647 folded before Flop
Seat 7: 56b0137c folded before Flop
Seat 8: cb195c66 collected (865)


Poker Hand #TM5543747356: Tournament #258198994, $25 GGMasters Bounty Warm-Up Special Hold'em No Limit - Level9(125/250) - 2026/02/04 00:29:32
Table '380' 8-max Seat #1 is the button
Seat 1: 7ec89b34 (2,693 in chips)
Seat 2: db2c203e (20,677 in chips)
Seat 3: 511f4d1c (24,006 in chips)
Seat 4: f113568e (8,083 in chips)
Seat 5: Hero (9,535 in chips)
Seat 6: e03b1647 (24,472 in chips)
Seat 7: 56b0137c (20,079 in chips)
Seat 8: cb195c66 (35,030 in chips)
e03b1647: posts the ante 30
511f4d1c: posts the ante 30
f113568e: posts the ante 30
7ec89b34: posts the ante 30
db2c203e: posts the ante 30
56b0137c: posts the ante 30
Hero: posts the ante 30
cb195c66: posts the ante 30
db2c203e: posts small blind 125
511f4d1c: posts big blind 250
*** HOLE CARDS ***
Dealt to 7ec89b34 
Dealt to db2c203e 
Dealt to 511f4d1c 
Dealt to f113568e 
Dealt to Hero [Qc 2s]
Dealt to e03b1647 
Dealt to 56b0137c 
Dealt to cb195c66 
f113568e: folds
Hero: folds
e03b1647: folds
56b0137c: raises 250 to 500
cb195c66: folds
7ec89b34: folds
db2c203e: calls 375
511f4d1c: folds
*** FLOP *** [Qs 9h Qd]
db2c203e: checks
56b0137c: bets 492
db2c203e: raises 1,133 to 1,625
56b0137c: calls 1,133
*** TURN *** [Qs 9h Qd] [6s]
db2c203e: bets 4,000
56b0137c: folds
Uncalled bet (4,000) returned to db2c203e
*** SHOWDOWN ***
db2c203e collected 4,740 from pot
*** SUMMARY ***
Total pot 4,740 | Rake 0 | Jackpot 0 | Bingo 0 | Fortune 0 | Tax 0
Board [Qs 9h Qd 6s]
Seat 1: 7ec89b34 (button) folded before Flop
Seat 2: db2c203e (small blind) won (4,740)
Seat 3: 511f4d1c (big blind) folded before Flop
Seat 4: f113568e folded before Flop
Seat 5: Hero folded before Flop
Seat 6: e03b1647 folded before Flop
Seat 7: 56b0137c folded on the Turn
Seat 8: cb195c66 folded before Flop


Poker Hand #TM5543747315: Tournament #258198994, $25 GGMasters Bounty Warm-Up Special Hold'em No Limit - Level9(125/250) - 2026/02/04 00:29:06
Table '380' 8-max Seat #8 is the button
Seat 1: 7ec89b34 (2,848 in chips)
Seat 2: db2c203e (20,342 in chips)
Seat 3: 511f4d1c (24,036 in chips)
Seat 4: f113568e (8,113 in chips)
Seat 5: Hero (9,565 in chips)
Seat 6: e03b1647 (24,502 in chips)
Seat 7: 56b0137c (20,109 in chips)
Seat 8: cb195c66 (35,060 in chips)
e03b1647: posts the ante 30
511f4d1c: posts the ante 30
f113568e: posts the ante 30
db2c203e: posts the ante 30
7ec89b34: posts the ante 30
56b0137c: posts the ante 30
Hero: posts the ante 30
cb195c66: posts the ante 30
7ec89b34: posts small blind 125
db2c203e: posts big blind 250
*** HOLE CARDS ***
Dealt to 7ec89b34 
Dealt to db2c203e 
Dealt to 511f4d1c 
Dealt to f113568e 
Dealt to Hero [4d 5c]
Dealt to e03b1647 
Dealt to 56b0137c 
Dealt to cb195c66 
511f4d1c: folds
f113568e: folds
Hero: folds
e03b1647: folds
56b0137c: folds
cb195c66: folds
7ec89b34: folds
Uncalled bet (125) returned to db2c203e
*** SHOWDOWN ***
db2c203e collected 490 from pot
*** SUMMARY ***
Total pot 490 | Rake 0 | Jackpot 0 | Bingo 0 | Fortune 0 | Tax 0
Seat 1: 7ec89b34 (small blind) folded before Flop
Seat 2: db2c203e (big blind) collected (490)
Seat 3: 511f4d1c folded before Flop
Seat 4: f113568e folded before Flop
Seat 5: Hero folded before Flop
Seat 6: e03b1647 folded before Flop
Seat 7: 56b0137c folded before Flop
Seat 8: cb195c66 (button) folded before Flop


Poker Hand #TM5543747296: Tournament #258198994, $25 GGMasters Bounty Warm-Up Special Hold'em No Limit - Level9(125/250) - 2026/02/04 00:28:46
Table '380' 8-max Seat #7 is the button
Seat 1: 7ec89b34 (2,513 in chips)
Seat 2: db2c203e (20,372 in chips)
Seat 3: 511f4d1c (24,066 in chips)
Seat 4: f113568e (8,143 in chips)
Seat 5: Hero (9,595 in chips)
Seat 6: e03b1647 (24,532 in chips)
Seat 7: 56b0137c (20,139 in chips)
Seat 8: cb195c66 (35,215 in chips)
e03b1647: posts the ante 30
511f4d1c: posts the ante 30
f113568e: posts the ante 30
db2c203e: posts the ante 30
7ec89b34: posts the ante 30
56b0137c: posts the ante 30
Hero: posts the ante 30
cb195c66: posts the ante 30
cb195c66: posts small blind 125
7ec89b34: posts big blind 250
*** HOLE CARDS ***
Dealt to 7ec89b34 
Dealt to db2c203e 
Dealt to 511f4d1c 
Dealt to f113568e 
Dealt to Hero [8s 3c]
Dealt to e03b1647 
Dealt to 56b0137c 
Dealt to cb195c66 
db2c203e: folds
511f4d1c: folds
f113568e: folds
Hero: folds
e03b1647: folds
56b0137c: folds
cb195c66: folds
Uncalled bet (125) returned to 7ec89b34
*** SHOWDOWN ***
7ec89b34 collected 490 from pot
*** SUMMARY ***
Total pot 490 | Rake 0 | Jackpot 0 | Bingo 0 | Fortune 0 | Tax 0
Seat 1: 7ec89b34 (big blind) collected (490)
Seat 2: db2c203e folded before Flop
Seat 3: 511f4d1c folded before Flop
Seat 4: f113568e folded before Flop
Seat 5: Hero folded before Flop
Seat 6: e03b1647 folded before Flop
Seat 7: 56b0137c (button) folded before Flop
Seat 8: cb195c66 (small blind) folded before Flop


Poker Hand #TM5543747256: Tournament #258198994, $25 GGMasters Bounty Warm-Up Special Hold'em No Limit - Level9(125/250) - 2026/02/04 00:28:17
Table '380' 8-max Seat #6 is the button
Seat 1: 7ec89b34 (2,543 in chips)
Seat 2: db2c203e (19,787 in chips)
Seat 3: 511f4d1c (24,096 in chips)
Seat 4: f113568e (8,173 in chips)
Seat 5: Hero (9,625 in chips)
Seat 6: e03b1647 (24,562 in chips)
Seat 7: 56b0137c (20,294 in chips)
Seat 8: cb195c66 (35,495 in chips)
e03b1647: posts the ante 30
511f4d1c: posts the ante 30
f113568e: posts the ante 30
db2c203e: posts the ante 30
7ec89b34: posts the ante 30
56b0137c: posts the ante 30
Hero: posts the ante 30
cb195c66: posts the ante 30
56b0137c: posts small blind 125
cb195c66: posts big blind 250
*** HOLE CARDS ***
Dealt to 7ec89b34 
Dealt to db2c203e 
Dealt to 511f4d1c 
Dealt to f113568e 
Dealt to Hero [6h Qh]
Dealt to e03b1647 
Dealt to 56b0137c 
Dealt to cb195c66 
7ec89b34: folds
db2c203e: raises 250 to 500
511f4d1c: folds
f113568e: folds
Hero: folds
e03b1647: folds
56b0137c: folds
cb195c66: folds
Uncalled bet (250) returned to db2c203e
*** SHOWDOWN ***
db2c203e collected 865 from pot
*** SUMMARY ***
Total pot 865 | Rake 0 | Jackpot 0 | Bingo 0 | Fortune 0 | Tax 0
Seat 1: 7ec89b34 folded before Flop
Seat 2: db2c203e collected (865)
Seat 3: 511f4d1c folded before Flop
Seat 4: f113568e folded before Flop
Seat 5: Hero folded before Flop
Seat 6: e03b1647 (button) folded before Flop
Seat 7: 56b0137c (small blind) folded before Flop
Seat 8: cb195c66 (big blind) folded before Flop


Poker Hand #TM5543747152: Tournament #258198994, $25 GGMasters Bounty Warm-Up Special Hold'em No Limit - Level8(100/200) - 2026/02/04 00:27:03
Table '380' 8-max Seat #5 is the button
Seat 1: 7ec89b34 (2,568 in chips)
Seat 2: db2c203e (21,412 in chips)
Seat 3: 511f4d1c (24,121 in chips)
Seat 4: f113568e (8,198 in chips)
Seat 5: Hero (9,650 in chips)
Seat 6: e03b1647 (24,687 in chips)
Seat 7: 56b0137c (17,819 in chips)
Seat 8: cb195c66 (36,120 in chips)
511f4d1c: posts the ante 25
e03b1647: posts the ante 25
f113568e: posts the ante 25
db2c203e: posts the ante 25
7ec89b34: posts the ante 25
56b0137c: posts the ante 25
Hero: posts the ante 25
cb195c66: posts the ante 25
e03b1647: posts small blind 100
56b0137c: posts big blind 200
*** HOLE CARDS ***
Dealt to 7ec89b34 
Dealt to db2c203e 
Dealt to 511f4d1c 
Dealt to f113568e 
Dealt to Hero [Jd 4h]
Dealt to e03b1647 
Dealt to 56b0137c 
Dealt to cb195c66 
cb195c66: raises 400 to 600
7ec89b34: folds
db2c203e: raises 1,000 to 1,600
511f4d1c: folds
f113568e: folds
Hero: folds
e03b1647: folds
56b0137c: raises 2,200 to 3,800
cb195c66: folds
db2c203e: folds
Uncalled bet (2,200) returned to 56b0137c
*** SHOWDOWN ***
56b0137c collected 4,100 from pot
*** SUMMARY ***
Total pot 4,100 | Rake 0 | Jackpot 0 | Bingo 0 | Fortune 0 | Tax 0
Seat 1: 7ec89b34 folded before Flop
Seat 2: db2c203e folded before Flop
Seat 3: 511f4d1c folded before Flop
Seat 4: f113568e folded before Flop
Seat 5: Hero (button) folded before Flop
Seat 6: e03b1647 (small blind) folded before Flop
Seat 7: 56b0137c (big blind) collected (4,100)
Seat 8: cb195c66 folded before Flop


Poker Hand #TM5543747101: Tournament #258198994, $25 GGMasters Bounty Warm-Up Special Hold'em No Limit - Level8(100/200) - 2026/02/04 00:26:20
Table '380' 8-max Seat #4 is the button
Seat 1: 7ec89b34 (2,593 in chips)
Seat 2: db2c203e (21,437 in chips)
Seat 3: 511f4d1c (24,146 in chips)
Seat 4: f113568e (8,223 in chips)
Seat 5: Hero (9,775 in chips)
Seat 6: e03b1647 (25,312 in chips)
Seat 7: 56b0137c (17,844 in chips)
Seat 8: cb195c66 (35,245 in chips)
511f4d1c: posts the ante 25
e03b1647: posts the ante 25
f113568e: posts the ante 25
db2c203e: posts the ante 25
7ec89b34: posts the ante 25
56b0137c: posts the ante 25
Hero: posts the ante 25
cb195c66: posts the ante 25
Hero: posts small blind 100
e03b1647: posts big blind 200
*** HOLE CARDS ***
Dealt to 7ec89b34 
Dealt to db2c203e 
Dealt to 511f4d1c 
Dealt to f113568e 
Dealt to Hero [9c 4c]
Dealt to e03b1647 
Dealt to 56b0137c 
Dealt to cb195c66 
56b0137c: folds
cb195c66: raises 400 to 600
7ec89b34: folds
db2c203e: folds
511f4d1c: folds
f113568e: folds
Hero: folds
e03b1647: calls 400
*** FLOP *** [Jc Ah 4d]
e03b1647: checks
cb195c66: bets 600
e03b1647: folds
Uncalled bet (600) returned to cb195c66
*** SHOWDOWN ***
cb195c66 collected 1,500 from pot
*** SUMMARY ***
Total pot 1,500 | Rake 0 | Jackpot 0 | Bingo 0 | Fortune 0 | Tax 0
Board [Jc Ah 4d]
Seat 1: 7ec89b34 folded before Flop
Seat 2: db2c203e folded before Flop
Seat 3: 511f4d1c folded before Flop
Seat 4: f113568e (button) folded before Flop
Seat 5: Hero (small blind) folded before Flop
Seat 6: e03b1647 (big blind) folded on the Flop
Seat 7: 56b0137c folded before Flop
Seat 8: cb195c66 won (1,500)


Poker Hand #TM5543747057: Tournament #258198994, $25 GGMasters Bounty Warm-Up Special Hold'em No Limit - Level8(100/200) - 2026/02/04 00:25:42
Table '380' 8-max Seat #3 is the button
Seat 1: 7ec89b34 (2,618 in chips)
Seat 2: db2c203e (21,462 in chips)
Seat 3: 511f4d1c (24,171 in chips)
Seat 4: f113568e (8,348 in chips)
Seat 5: Hero (10,000 in chips)
Seat 6: e03b1647 (25,337 in chips)
Seat 7: 56b0137c (17,869 in chips)
Seat 8: cb195c66 (34,770 in chips)
511f4d1c: posts the ante 25
e03b1647: posts the ante 25
f113568e: posts the ante 25
db2c203e: posts the ante 25
7ec89b34: posts the ante 25
56b0137c: posts the ante 25
Hero: posts the ante 25
cb195c66: posts the ante 25
f113568e: posts small blind 100
Hero: posts big blind 200
*** HOLE CARDS ***
Dealt to 7ec89b34 
Dealt to db2c203e 
Dealt to 511f4d1c 
Dealt to f113568e 
Dealt to Hero [6s 7c]
Dealt to e03b1647 
Dealt to 56b0137c 
Dealt to cb195c66 
e03b1647: folds
56b0137c: folds
cb195c66: raises 400 to 600
7ec89b34: folds
db2c203e: folds
511f4d1c: folds
f113568e: folds
Hero: folds
Uncalled bet (400) returned to cb195c66
*** SHOWDOWN ***
cb195c66 collected 700 from pot
*** SUMMARY ***
Total pot 700 | Rake 0 | Jackpot 0 | Bingo 0 | Fortune 0 | Tax 0
Seat 1: 7ec89b34 folded before Flop
Seat 2: db2c203e folded before Flop
Seat 3: 511f4d1c (button) folded before Flop
Seat 4: f113568e (small blind) folded before Flop
Seat 5: Hero (big blind) folded before Flop
Seat 6: e03b1647 folded before Flop
Seat 7: 56b0137c folded before Flop
Seat 8: cb195c66 collected (700)
"""

# --- 1. 頁面設定 ---
st.set_page_config(page_title="Poker Copilot War Room", page_icon="♠️", layout="wide")

# --- CSS: Apple HIG macOS Dark Mode ---
st.markdown("""
<style>
    /* 1. Typography — Inter + Noto Sans TC for clean Latin & Chinese (Minduck-style) */
    .stApp {
        background-color: #1c1c1e;
        font-family: 'Inter', 'Noto Sans TC', 'Microsoft JhengHei', sans-serif;
        font-weight: 400;
        line-height: 1.6;
        letter-spacing: 0.05em;
        -webkit-font-smoothing: antialiased;
    }
    .stApp h1 { font-weight: 700; color: rgba(255,255,255,0.95); }
    .stApp h2, .stApp h3 { font-weight: 600; color: rgba(255,255,255,0.9); }
    .stApp p, .stApp span { color: rgba(255,255,255,0.85); }

    /* 2. Hide Streamlit chrome */
    header[data-testid="stHeader"] { visibility: hidden; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }

    /* 3. Metrics — Apple Stocks style: large, thin, crisp */
    div[data-testid="stMetricValue"] {
        font-size: 34px !important;
        font-weight: 300 !important;
        color: #30D158 !important;
        letter-spacing: -0.5px;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 13px !important;
        color: rgba(255,255,255,0.55) !important;
        font-weight: 500;
    }
    div[data-testid="stMetricDelta"] {
        color: #FF453A !important;
        font-weight: 500;
    }

    /* 4. Buttons — Pill shape, iOS-style gradient */
    div.stButton > button {
        font-family: 'Inter', 'Noto Sans TC', 'Microsoft JhengHei', sans-serif;
        border-radius: 99px !important;
        font-weight: 600;
        transition: opacity 0.2s ease, transform 0.15s ease;
    }
    div.stButton > button[kind="primary"] {
        background: linear-gradient(180deg, #0A84FF 0%, #0066CC 100%) !important;
        border: 1px solid rgba(255,255,255,0.12);
        color: #fff !important;
    }
    div.stButton > button[kind="primary"]:hover {
        opacity: 0.92;
        transform: scale(1.02);
    }
    div.stButton > button:not([kind="primary"]) {
        background: rgba(255,255,255,0.08) !important;
        border: 1px solid rgba(255,255,255,0.1);
        color: rgba(255,255,255,0.9) !important;
    }

    /* 5. Sidebar — Glassmorphism */
    section[data-testid="stSidebar"] {
        background: rgba(28, 28, 30, 0.72) !important;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255,255,255,0.08);
    }
    section[data-testid="stSidebar"] * { color: rgba(255,255,255,0.85); }

    /* 6. Tabs — Minimal, weight hierarchy */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        border-bottom: 1px solid rgba(255,255,255,0.08);
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        background: transparent;
        border: none;
        color: rgba(255,255,255,0.5);
        font-weight: 500;
        font-family: 'Inter', 'Noto Sans TC', 'Microsoft JhengHei', sans-serif;
    }
    .stTabs [aria-selected="true"] {
        color: #0A84FF !important;
        font-weight: 600;
        border-bottom: 2px solid #0A84FF !important;
    }

    /* 7. Cards / Containers — Glass + depth border (Leak Detector, etc.) */
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
        background: rgba(44, 44, 46, 0.6);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 16px;
    }

    /* 8. Blockquote (教練狠評) */
    blockquote {
        background: rgba(44, 44, 46, 0.7);
        border: 1px solid rgba(255,255,255,0.08);
        border-left: 4px solid #0A84FF;
        padding: 16px 20px;
        border-radius: 10px;
        color: rgba(255,255,255,0.9);
        font-size: 15px;
        margin: 20px 0;
    }

    /* 9. Dataframe — Apple Numbers style: clean headers, minimal grid */
    div[data-testid="stDataFrame"] {
        background: rgba(44, 44, 46, 0.5) !important;
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 10px;
        overflow: hidden;
    }
    div[data-testid="stDataFrame"] table {
        border-collapse: collapse;
        font-family: 'Inter', 'Noto Sans TC', 'Microsoft JhengHei', sans-serif;
    }
    div[data-testid="stDataFrame"] th {
        background: rgba(255,255,255,0.06) !important;
        color: rgba(255,255,255,0.9) !important;
        font-weight: 600;
        font-size: 12px;
        text-transform: none;
        letter-spacing: 0.2px;
        border-bottom: 1px solid rgba(255,255,255,0.12);
        padding: 10px 14px;
    }
    div[data-testid="stDataFrame"] td {
        border-bottom: 1px solid rgba(255,255,255,0.06);
        color: rgba(255,255,255,0.85);
        padding: 10px 14px;
        font-size: 13px;
    }
    div[data-testid="stDataFrame"] tr:hover td {
        background: rgba(255,255,255,0.04);
    }

    /* 10. Hand History — Chat (HIG-aligned colors) */
    .hand-chat-container { max-width: 100%; padding: 8px 0; }
    .hand-chat-header {
        text-align: center;
        font-size: 13px;
        font-weight: 500;
        color: rgba(255,255,255,0.55);
        margin-bottom: 12px;
        padding: 10px 14px;
        background: rgba(44, 44, 46, 0.6);
        backdrop-filter: blur(12px);
        border-radius: 10px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    .hand-chat-street-badge { text-align: center; margin: 14px 0 10px 0; }
    .hand-chat-street-badge .street-label {
        font-size: 11px;
        font-weight: 600;
        color: rgba(255,255,255,0.5);
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 6px;
    }
    .hand-chat-street-badge .street-cards { display: flex; justify-content: center; align-items: center; flex-wrap: wrap; gap: 4px; }
    .hand-chat-bubble {
        max-width: 85%;
        padding: 10px 16px;
        border-radius: 16px;
        font-size: 13px;
        line-height: 1.4;
        margin: 5px 0;
        word-break: break-word;
        font-family: 'Inter', 'Noto Sans TC', 'Microsoft JhengHei', sans-serif;
    }
    .hand-chat-bubble.chat-left {
        background: rgba(58, 58, 60, 0.9);
        color: rgba(255,255,255,0.9);
        margin-right: auto;
        border-bottom-left-radius: 4px;
        border: 1px solid rgba(255,255,255,0.08);
    }
    .hand-chat-bubble.chat-right {
        background: linear-gradient(180deg, rgba(10, 132, 255, 0.35) 0%, rgba(0, 102, 204, 0.4) 100%);
        color: #fff;
        margin-left: auto;
        border-bottom-right-radius: 4px;
        border: 1px solid rgba(255,255,255,0.15);
    }
    .hand-chat-bubble .actor { font-weight: 600; }
    .card-badge-chat {
        display: inline-block;
        padding: 3px 8px;
        margin: 0 2px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 13px;
        background: rgba(255,255,255,0.95);
        border: 1px solid rgba(0,0,0,0.08);
    }
    .card-badge-chat.red { color: #D32F2F; }
    .card-badge-chat.black { color: #1c1c1e; }
</style>
""", unsafe_allow_html=True)

st.title("♠️ Poker Copilot War Room")
st.caption("🚀 AI 驅動的德州撲克戰術分析系統 | 你的 24/7 私人教練")

# 單手分析時的隨機等待文案
LOADING_TEXTS = [
    "正在計算死錢賠率...",
    "正在分析對手範圍...",
    "正在回顧 GTO 策略...",
    "AI 教練正在思考最佳打法...",
]


# --- 2. 側邊欄：驗證與設定 ---
with st.sidebar:
    st.header("🔐 身份驗證")
    user_password = st.text_input("輸入通關密碼 (Access Code)", type="password")
    api_key = None
    
    if user_password == st.secrets["ACCESS_PASSWORD"]:
        st.success("✅ 驗證通過！")
        api_key = st.secrets["GEMINI_API_KEY"]
    elif user_password:
        st.error("❌ 密碼錯誤")

    st.divider()

    if api_key:
        st.header("⚙️ 設定")
        selected_model = st.selectbox("AI 引擎", ["gemini-2.5-flash"])
    st.markdown("---")
    st.link_button("💬 許願 / 回報 Bug", "https://docs.google.com/forms/d/e/1FAIpQLSeiQT3WgoxLXqfn6eMrvQkS5lBTewgl9iS9AkxQuMyGTySESA/viewform", use_container_width=True)

# --- 3. 核心功能函數 (修復版) ---

def load_content(uploaded_file):
    if uploaded_file is not None:
        return uploaded_file.getvalue().decode("utf-8")
    return None

def cards_to_emoji(cards_str):
    """
    將撲克牌字串轉換為 Emoji 格式
    例如: "Ah Ks" -> "A♥️ K♠️"
    """
    if not cards_str:
        return "Unknown"
    
    suit_map = {
        'h': '♥️',  # Hearts 紅心
        'd': '♦️',  # Diamonds 方塊
        'c': '♣️',  # Clubs 梅花
        's': '♠️'   # Spades 黑桃
    }
    
    cards = cards_str.split()
    emoji_cards = []
    
    for card in cards:
        if len(card) >= 2:
            rank = card[:-1]  # 牌面 (A, K, Q, J, T, 9, 8...)
            suit = card[-1].lower()  # 花色 (h, d, c, s)
            emoji_cards.append(f"{rank}{suit_map.get(suit, suit)}")
    
    return " ".join(emoji_cards)

# 花色對應（與 cards_to_emoji 一致，供 parse_hands 產出 hero_cards_emoji）
SUIT_EMOJI = {'c': '♣️', 's': '♠️', 'h': '♥️', 'd': '♦️'}


def _card_badge(card_str):
    """單張牌 → 帶顏色的 HTML badge。紅心/方塊紅，黑桃/梅花灰藍。"""
    card_str = card_str.strip()
    if len(card_str) < 2:
        return ""
    rank, suit = card_str[:-1], card_str[-1].lower()
    if suit in ("h", "d"):
        color = "#e74c3c"
        border = "#c0392b"
    else:
        color = "#3498db"
        border = "#2980b9"
    emoji = SUIT_EMOJI.get(suit, "")
    label = html.escape(f"{rank}{emoji}")
    return f'<span class="timeline-card" style="background:{color};border-color:{border}">{label}</span>'


def _card_badge_chat(card_str):
    """單張牌 → 聊天風格 HTML badge：白底，紅心/方塊紅字，黑桃/梅花黑字。"""
    card_str = card_str.strip()
    if len(card_str) < 2:
        return ""
    rank, suit = card_str[:-1], card_str[-1].lower()
    cls = "card-badge-chat red" if suit in ("h", "d") else "card-badge-chat black"
    emoji = SUIT_EMOJI.get(suit, "")
    label = html.escape(f"{rank}{emoji}")
    return f'<span class="{cls}">{label}</span>'


def render_hand_history_timeline(hand_content, hero_name="Hero"):
    """
    將手牌 log 解析為「聊天介面」風格：只顯示重要下注與公牌，對手左灰泡、Hero 右綠泡。
    顯示 Level/Blinds 標題、玩家 ID 換成桌位、籌碼換成 BB。
    """
    if not hand_content or not hand_content.strip():
        st.caption("無手牌內容")
        return

    # --- 1. 解析 Level / Blinds（標題與 BB 換算）---
    level_match = re.search(r"Level(\d+)\(([\d,]+)/([\d,]+)\)", hand_content)
    if level_match:
        level_num = level_match.group(1)
        sb_str = level_match.group(2).replace(",", "")
        bb_str = level_match.group(3).replace(",", "")
        bb_size = int(bb_str) if bb_str else 400
        header_text = f"🏆 Level: {level_num} | Blinds: {sb_str}/{bb_str}"
    else:
        bb_fallback = re.search(r"posts big blind ([\d,]+)", hand_content)
        bb_size = int(bb_fallback.group(1).replace(",", "")) if bb_fallback else 400
        header_text = f"🏆 Blinds: —/{bb_size}"

    # --- 2. 建立 Player ID -> 桌位 對照（Seat #X is the button + Seat X: playerId）---
    btn_match = re.search(r"Seat #(\d+) is the button", hand_content)
    button_seat = int(btn_match.group(1)) if btn_match else None
    seats_dict = {}
    for m in re.finditer(r"Seat (\d+): (\S+)", hand_content):
        sn, pid = m.group(1), m.group(2)
        if sn not in seats_dict:
            seats_dict[sn] = pid
    total_seats = sorted([int(s) for s in seats_dict.keys()]) if seats_dict else []
    id_to_position = {}
    for sn in total_seats:
        pid = seats_dict[str(sn)]
        id_to_position[pid] = calculate_position(sn, button_seat, total_seats)
    id_to_position[hero_name] = "Hero"

    def to_bb(amount_str):
        try:
            return int(amount_str.replace(",", "")) / bb_size if bb_size else 0
        except (ValueError, AttributeError):
            return 0

    def format_action_bb(line):
        """將行內籌碼數字改為 BB（1 位小數）。"""
        # raises X to Y [and is all-in]
        line = re.sub(
            r"raises ([\d,]+) to ([\d,]+)( and is all-in)?",
            lambda m: f"raises {to_bb(m.group(1)):.1f} to {to_bb(m.group(2)):.1f} BB" + (m.group(3) or ""),
            line,
        )
        line = re.sub(r"bets ([\d,]+)", lambda m: f"bets {to_bb(m.group(1)):.1f} BB", line)
        line = re.sub(
            r"calls ([\d,]+)( and is all-in)?",
            lambda m: f"calls {to_bb(m.group(1)):.1f} BB" + (m.group(2) or ""),
            line,
        )
        return line

    def replace_speaker_with_position(line):
        """將行首的 Player ID 換成桌位（或 Hero）。"""
        if ": " not in line:
            return line
        speaker, rest = line.split(": ", 1)
        speaker = speaker.strip()
        pos = id_to_position.get(speaker, speaker)
        return f"{pos}: {rest}"

    # 噪音過濾：含這些關鍵字的行不顯示
    IGNORE_SUBSTRINGS = [
        "posts the ante", "in chips", "returned to", "collected", "summary",
        "table", "seat", "posts small blind", "posts big blind", "Dealt to",
        "Uncalled", "Total pot", "Board ", "Seat ", "shows ", "won (",
        "and lost", "and won", "folded before", "folded on",
    ]

    def should_ignore_line(line):
        low = line.lower()
        for sub in IGNORE_SUBSTRINGS:
            if sub.lower() in low:
                return True
        return False

    def is_hero_line(line):
        return line.strip().startswith(hero_name + ":")

    def is_active_action(line):
        """只保留：bets, calls, raises, checks, all-in；以及 Hero 的 folds。"""
        if "folds" in line:
            return is_hero_line(line)
        for verb in ("bets", "calls", "raises", "checks", "all-in"):
            if verb in line:
                return True
        return False

    # 依 *** STREET *** 分段
    parts = re.split(r"\n\s*\*\*\* (HOLE CARDS|FLOP|TURN|RIVER|SHOWDOWN|SUMMARY) \*\*\*\s*\n?", hand_content)
    segments = []
    for i in range(1, len(parts) - 1, 2):
        if i + 1 < len(parts):
            street_name = parts[i].strip()
            body = (parts[i + 1] or "").strip()
            segments.append((street_name, body))

    out = ['<div class="hand-chat-container">']
    out.append(f'<div class="hand-chat-header">{html.escape(header_text)}</div>')

    for street_name, body in segments:
        if street_name in ("SHOWDOWN", "SUMMARY"):
            continue

        lines = [ln.strip() for ln in body.split("\n") if ln.strip()]
        first_line = lines[0] if lines else ""
        start_idx = 0

        if street_name in ("FLOP", "TURN", "RIVER"):
            board_cards = re.findall(r"\[([A-Za-z0-9\s]+)\]", first_line)
            if board_cards:
                out.append('<div class="hand-chat-street-badge">')
                out.append(f'<div class="street-label">*** {street_name} ***</div>')
                out.append('<div class="street-cards">')
                for bracket in board_cards:
                    for card in bracket.split():
                        if re.match(r"^[AKQJT2-9][hdcs]$", card, re.IGNORECASE):
                            out.append(_card_badge_chat(card))
                out.append("</div></div>")
                start_idx = 1

        for line in lines[start_idx:]:
            if should_ignore_line(line) or not is_active_action(line):
                continue
            line = replace_speaker_with_position(line)
            line = format_action_bb(line)
            line_safe = html.escape(line)
            is_hero = line.strip().startswith("Hero:")
            bubble_cls = "hand-chat-bubble chat-right" if is_hero else "hand-chat-bubble chat-left"
            out.append(f'<div class="{bubble_cls}">{line_safe}</div>')

    out.append("</div>")
    st.markdown("".join(out), unsafe_allow_html=True)


def calculate_position(hero_seat, button_seat, total_seats):
    """
    數學定義位置：依順時針距離 Button 計算。
    輸入：hero_seat (int), button_seat (int), total_seats (list[int]，已排序之所有玩家座號)。
    距離公式：(hero_idx - btn_idx) % count
    定義：0=BTN, 1=SB, 2=BB, 3=UTG, 4=UTG+1(6人+), 倒數第1=CO, 倒數第2=HJ, 其他=MP
    """
    if not total_seats or hero_seat is None or button_seat is None:
        return "Other"
    try:
        hero_seat = int(hero_seat)
        button_seat = int(button_seat)
        total_seats = sorted([int(s) for s in total_seats])
    except (TypeError, ValueError):
        return "Other"
    
    if hero_seat not in total_seats or button_seat not in total_seats:
        return "Other"
    
    n = len(total_seats)
    btn_idx = total_seats.index(button_seat)
    hero_idx = total_seats.index(hero_seat)
    distance = (hero_idx - btn_idx) % n
    
    if distance == 0:
        return "BTN"
    if distance == 1:
        return "SB"
    if distance == 2:
        return "BB"
    if distance == 3:
        return "UTG"
    if distance == 4 and n >= 6:
        return "UTG+1"
    if distance == n - 1:
        return "CO"
    if distance == n - 2:
        return "HJ"
    if 5 <= distance <= n - 3:
        return "MP"
    return "Other"

def distance_to_button(seat, button_seat, total_seats):
    """
    順時針距離 Button 的步數（0=BTN, 1=SB, 2=BB, 3=UTG, ...）。
    翻後行動順序為 SB→BB→UTG→...→BTN，故數字越大代表動作越晚 → In Position。
    """
    if not total_seats or seat is None or button_seat is None or seat not in total_seats or button_seat not in total_seats:
        return None
    sorted_seats = sorted([int(s) for s in total_seats])
    n = len(sorted_seats)
    btn_idx = sorted_seats.index(int(button_seat))
    seat_idx = sorted_seats.index(int(seat))
    return (seat_idx - btn_idx) % n

def parse_hands(content):
    """
    專為 GGPoker 格式設計的手牌解析器
    參考檔案: GGtest.txt
    """
    # 切割手牌：以 "Poker Hand #" 為分隔符
    raw_hands = re.split(r"(?=Poker Hand #)", content)
    parsed_hands = []
    detected_hero = None

    for raw_hand in raw_hands:
        if not raw_hand.strip() or len(raw_hand) < 100:
            continue
        
        full_hand_text = raw_hand.strip()
        
        # 1. 抓取手牌 ID (格式: "Poker Hand #TM5492660659:" 或 "Poker Hand #DEMO_TRAP:")
        hand_id_match = re.search(r"Poker Hand #(TM\d+|[A-Za-z0-9_]+):", full_hand_text)
        hand_id = hand_id_match.group(1) if hand_id_match else "Unknown"
        
        # 2. 抓取 Big Blind 大小 (GGPoker: "Level19(1,750/3,500)" / Demo: "posts big blind 400")
        bb_size_match = re.search(r"Level\d+\([\d,]+/([\d,]+)\)", full_hand_text)
        if bb_size_match:
            bb_size = int(bb_size_match.group(1).replace(",", ""))
        else:
            bb_fallback = re.search(r"posts big blind ([\d,]+)", full_hand_text)
            bb_size = int(bb_fallback.group(1).replace(",", "")) if bb_fallback else 400
        
        # 3. 抓取 Hero 名字與手牌
        # GGPoker 格式：只有 Hero 會有 "Dealt to <Name> [牌]"，其他玩家是 "Dealt to <Name>" (無牌或空)
        # 關鍵：找有實際手牌的那行 (中括號內有內容)
        hero_match = re.search(r"Dealt to (\S+) \[([A-Za-z0-9]{2} [A-Za-z0-9]{2})\]", full_hand_text)
        current_hero = hero_match.group(1) if hero_match else None
        hero_cards = hero_match.group(2) if hero_match else None
        
        if current_hero and detected_hero is None:
            detected_hero = current_hero
        
        # 如果找不到 Hero，跳過此手牌
        if not current_hero:
            continue
        
        # 4. 抓取 Hero 的起始籌碼 (GGPoker: "in chips" / Demo: "Seat 1: Hero (40000)")
        stack_pattern = rf"Seat \d+: {re.escape(current_hero)} \(([\d,]+)(?: in chips)?\)"
        stack_match = re.search(stack_pattern, full_hand_text)
        hero_chips = int(stack_match.group(1).replace(",", "")) if stack_match else 0
        bb_count = round(hero_chips / bb_size, 1) if bb_size > 0 else 0
        
        # 5. 計算 VPIP/PFR（僅翻牌前 Pre-flop）
        # 以 "*** FLOP ***" 切割，只對第一部分做匹配，避免翻後動作誤算
        preflop_text = full_hand_text.split("*** FLOP ***")[0] if "*** FLOP ***" in full_hand_text else full_hand_text
        
        is_vpip = False
        is_pfr = False
        hero_escaped = re.escape(current_hero)
        
        # VPIP: 翻牌前 Hero 有 raises / calls / bets（排除 posts）
        vpip_pattern = rf"^{hero_escaped}: (raises|calls|bets)"
        if re.search(vpip_pattern, preflop_text, re.MULTILINE):
            is_vpip = True
        
        # PFR: 翻牌前 Hero 有 raises
        pfr_pattern = rf"^{hero_escaped}: raises"
        if re.search(pfr_pattern, preflop_text, re.MULTILINE):
            is_pfr = True
        
        # 6. 手牌花色與牌型（同花判定 + 牌型標籤）
        is_suited = False
        hand_type = None
        is_pair = False
        is_ax = False
        is_broadway = False
        if hero_cards:
            cards = hero_cards.split()
            if len(cards) >= 2:
                suit1 = cards[0][-1].lower()
                suit2 = cards[1][-1].lower()
                is_suited = (suit1 == suit2)
                rank_order = "AKQJT98765432"
                broadway_ranks = "AKQJT"
                r1, r2 = cards[0][:-1].upper(), cards[1][:-1].upper()
                is_pair = (r1 == r2)
                is_ax = (r1 == "A" or r2 == "A")
                is_broadway = (r1 in broadway_ranks and r2 in broadway_ranks)
                if r1 not in rank_order or r2 not in rank_order:
                    hand_type = f"{r1}{r2}{'s' if is_suited else 'o'}"
                else:
                    high, low = (r1, r2) if rank_order.index(r1) < rank_order.index(r2) else (r2, r1)
                    hand_type = f"{high}{low}{'s' if is_suited else 'o'}"
        
        # 7. 抓取底池大小 (GGPoker: "Total pot 1,250" / Demo: "collected 12000 from pot" or "won (40000)")
        pot_match = re.search(r"Total pot ([\d,]+)", full_hand_text)
        if pot_match:
            pot_size = int(pot_match.group(1).replace(",", ""))
        else:
            collected = re.search(r"collected ([\d,]+) from pot", full_hand_text)
            won = re.search(r"won \(([\d,]+)\)", full_hand_text)
            pot_size = int((collected or won).group(1).replace(",", "")) if (collected or won) else 0
        
        # 8. 精準抓取座位並用數學計算位置（完全移除 AI 對位置的解釋權）
        btn_match = re.search(r"The button is in seat #(\d+)", full_hand_text) or re.search(r"Seat #(\d+) is the button", full_hand_text)
        button_seat = int(btn_match.group(1)) if btn_match else None
        hero_seat_match = re.search(rf"Seat (\d+): {re.escape(current_hero)}\s", full_hand_text)
        hero_seat = int(hero_seat_match.group(1)) if hero_seat_match else None
        # 【修正點】放寬正則表達式，只要是 "Seat X:" 開頭的都算入座位，不再檢查括號內的籌碼格式
        active_seats = list(set(int(m.group(1)) for m in re.finditer(r"Seat (\d+):", full_hand_text)))
        hero_position_str = calculate_position(hero_seat, button_seat, active_seats)
        hero_dist = distance_to_button(hero_seat, button_seat, active_seats)
        dist_to_name = {0: "BTN", 1: "SB", 2: "BB", 3: "UTG", 4: "UTG+1", 5: "MP", 6: "MP+1", 7: "CO"}
        position_name = dist_to_name.get(hero_dist, "Early") if hero_dist is not None else "Early"
        
        # 8b. 主要對手 (Main Villain) 與相對位置 (IP/OOP)
        villain_seat = None
        relative_pos_str = "N/A"
        m_raise = re.search(r"(\S+): raises", preflop_text)
        m_bet = re.search(r"(\S+): bets", preflop_text)
        villain_name = None
        if m_raise and m_bet:
            villain_name = m_raise.group(1) if m_raise.start() < m_bet.start() else m_bet.group(1)
        elif m_raise:
            villain_name = m_raise.group(1)
        elif m_bet:
            villain_name = m_bet.group(1)
        if villain_name:
            if villain_name == current_hero:
                relative_pos_str = "Hero 為翻前加注者 (無單一主要對手)"
            else:
                villain_seat_m = re.search(rf"Seat (\d+): {re.escape(villain_name)}\s", full_hand_text)
                if villain_seat_m and active_seats:
                    villain_seat = int(villain_seat_m.group(1))
                    if villain_seat in active_seats:
                        hero_dist = distance_to_button(hero_seat, button_seat, active_seats)
                        villain_dist = distance_to_button(villain_seat, button_seat, active_seats)
                        if hero_dist is not None and villain_dist is not None:
                            if hero_dist == 0:
                                relative_pos_str = "In Position (IP)"  # Hero 是 Button
                            elif villain_dist == 0:
                                relative_pos_str = "Out of Position (OOP)"  # 對手是 Button
                            elif hero_dist > villain_dist:
                                relative_pos_str = "In Position (IP)"  # Hero 距離更大 = 動作更晚
                            else:
                                relative_pos_str = "Out of Position (OOP)"
                    else:
                        relative_pos_str = "N/A (無法判定主要對手座位)"
                else:
                    relative_pos_str = "N/A (無法判定主要對手座位)"
        else:
            relative_pos_str = "多路底池 (無人加注)"
        
        # 9. 花色轉換：c=♣️, s=♠️, h=♥️, d=♦️，直接產出 hero_cards_emoji 存入字典
        hero_cards_emoji = "Unknown"
        if hero_cards:
            parts = hero_cards.split()
            emoji_parts = [f"{c[:-1]}{SUIT_EMOJI.get(c[-1].lower(), c[-1])}" for c in parts if len(c) >= 2]
            hero_cards_emoji = " ".join(emoji_parts) if emoji_parts else "Unknown"
        
        # 10. 輸贏結果偵測（Hero collected / won / matches → win；有 VPIP 未贏 → loss；未入池 → fold）
        hero_win_pattern = rf"{re.escape(current_hero)}\s+(collected|won|wins|matches)"
        if re.search(hero_win_pattern, full_hand_text, re.IGNORECASE):
            result = "win"
        elif is_vpip:
            result = "loss"
        else:
            result = "fold"
        
        is_winner = (result == "win")
        total_pot = pot_size  # 與 pot_size 一致，供智慧抓漏使用
        
        parsed_hands.append({
            "id": hand_id,
            "content": full_hand_text,
            "vpip": is_vpip,
            "pfr": is_pfr,
            "bb": bb_count,
            "hero": current_hero,
            "hero_cards": hero_cards,
            "hero_cards_emoji": hero_cards_emoji,
            "is_suited": is_suited,
            "hand_type": hand_type,
            "pot_size": pot_size,
            "position": hero_position_str,
            "villain_seat": villain_seat,
            "relative_pos_str": relative_pos_str,
            "result": result,
            "is_winner": is_winner,
            "total_pot": total_pot,
            "bb_size": bb_size,
            "is_pair": is_pair,
            "is_ax": is_ax,
            "is_broadway": is_broadway,
            "position_name": position_name,
        })
    
    return parsed_hands, detected_hero

def generate_match_summary(hands_data, vpip, pfr, api_key, model):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    total_hands = len(hands_data)
    vpip_count = sum(1 for h in hands_data if h.get("vpip"))
    pfr_count = sum(1 for h in hands_data if h.get("pfr"))
    agg_freq = round((pfr_count / vpip_count) * 100, 1) if vpip_count > 0 else 0.0

    # 位置分組：EP=UTG+UTG+1, MP=MP+MP+1+HJ
    POS_GROUPS = {
        "BTN": ["BTN"],
        "SB": ["SB"],
        "BB": ["BB"],
        "EP": ["UTG", "UTG+1"],
        "MP": ["MP", "MP+1", "HJ"],
        "CO": ["CO"],
    }

    def calc_pos_stats(pos_keys):
        hands_in_pos = [h for h in hands_data if h.get("position") in pos_keys or h.get("position_name") in pos_keys]
        n = len(hands_in_pos)
        if n == 0:
            return "N/A", "N/A", 0
        v = sum(1 for h in hands_in_pos if h.get("vpip"))
        p = sum(1 for h in hands_in_pos if h.get("pfr"))
        vpip_pct = round((v / n) * 100, 1)
        pfr_pct = round((p / n) * 100, 1)
        return vpip_pct, pfr_pct, n

    vpip_btn, pfr_btn, _ = calc_pos_stats(POS_GROUPS["BTN"])
    vpip_sb, pfr_sb, _ = calc_pos_stats(POS_GROUPS["SB"])
    vpip_bb, pfr_bb, _ = calc_pos_stats(POS_GROUPS["BB"])
    vpip_ep, pfr_ep, _ = calc_pos_stats(POS_GROUPS["EP"])
    vpip_mp, pfr_mp, _ = calc_pos_stats(POS_GROUPS["MP"])
    vpip_co, pfr_co, _ = calc_pos_stats(POS_GROUPS["CO"])

    def fmt_pos(vpip_val, pfr_val):
        if vpip_val == "N/A" or pfr_val == "N/A":
            return "N/A"
        return f"VPIP {vpip_val}% / PFR {pfr_val}%"

    # 關鍵手牌篩選：vpip == True，依 pot_size（底池大小）由大到小排序，取前 5 手最大底池
    key_hands_raw = [h for h in hands_data if h.get("vpip")]
    key_hands_raw.sort(key=lambda h: h.get("pot_size", 0), reverse=True)
    key_hands = key_hands_raw[:5]
    
    # 組關鍵手牌描述：一律使用 Hand #<display_index>（與 UI 列表一致），不顯示 TM... 原始 ID
    key_hands_lines = []
    for i, h in enumerate(key_hands, 1):
        display_idx = h.get("display_index", i)
        hero_cards = h.get("hero_cards") or "??"
        suited_label = "(Suited)" if h.get("is_suited") else "(Offsuit)"
        ht = h.get("hand_type") or "??"
        pot_size = h.get("pot_size", 0)
        key_hands_lines.append(
            f"【Hand #{display_idx}】\n"
            f"- Hero 底牌: {hero_cards} {suited_label} (牌型: {ht})\n"
            f"- 底池: {pot_size}\n"
            f"- 完整紀錄:\n{h.get('content', '')}"
        )
    
    key_hands_text = "\n\n---\n\n".join(key_hands_lines) if key_hands_lines else "（無 VPIP 手牌）"
    
    prompt = f"""你是一位專業且資深的撲克導師。語氣要求：專業、冷靜、客觀，帶有建設性。請勿使用「兄弟」、「喔！」、「秀肌肉」等過於輕浮或江湖味的詞彙。

---

【整體數據】
- 總手牌數: {total_hands}
- VPIP: {vpip:.1f}% | PFR: {pfr:.1f}% | Agg: {agg_freq:.1f}%

【位置別數據 (Positional Stats)】
- BTN: {fmt_pos(vpip_btn, pfr_btn)}
- SB:  {fmt_pos(vpip_sb, pfr_sb)}
- BB:  {fmt_pos(vpip_bb, pfr_bb)}
- EP:  {fmt_pos(vpip_ep, pfr_ep)}
- MP:  {fmt_pos(vpip_mp, pfr_mp)}
- CO:  {fmt_pos(vpip_co, pfr_co)}

【關鍵手牌（共 5 手，依底池大小選出）】
以下手牌編號為 Hand #數字，與使用者介面列表完全對應。請依此編號引用，勿使用 TM 等原始 ID。手牌已標註 (Suited) 或 (Offsuit)，請依此解讀花色。

{key_hands_text}

---

【輸出格式】請務必依以下三個區塊、用 Markdown 撰寫：

## 🎯 賽事回顧
請寫一段約 150～200 字的完整段落，像賽後新聞稿一樣，專業地總結選手的風格（鬆/緊、被動/激進）以及本場比賽的主要漏洞。**務必結合「位置別數據」指出特定位置的漏洞**（例如 BB 防守過緊、BTN 開池過少等）。不要只寫一句話。

## 🔥 關鍵戰役覆盤
針對上述 5 手大底池手牌，分析 Hero 在大底池處理上的優缺點。每當提到某一手時，必須標註「Hand #數字」（例如 Hand #3、Hand #12），與介面列表一致。

## 💡 下場比賽調整
給出 1～2 個具體可執行的建議。"""
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1}
    }
    try:
        resp = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
        return resp.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        return "AI 連線失敗，請檢查 API Key 或稍後再試。"

def analyze_specific_hand(hand_data, api_key, model):
    """
    傳入完整 hand_data；花色與位置由系統事實強制注入，AI 無解釋權。
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    hero_cards_emoji = hand_data.get("hero_cards_emoji") or cards_to_emoji(hand_data.get("hero_cards"))
    hero_position = hand_data.get("position", "Other")
    bb_count = hand_data.get("bb", 0)
    display_index = hand_data.get("display_index", "?")
    relative_pos_str = hand_data.get("relative_pos_str", "N/A")
    
    fact_sheet = f"""【系統判定事實 - 分析基準，請嚴格遵守】
- Hero 手牌: {hero_cards_emoji}
- Hero 位置: {hero_position}
- 籌碼量: {bb_count} BB
- 相對位置優劣: {relative_pos_str} (針對主要對手)
若原始文本與上述衝突，以上述為準。輸出時請勿重複列出此清單，直接進入分析。

**相對位置思考限制**：你必須基於上述的「相對位置優劣」進行分析，嚴禁自行推斷 Hero 是 IP 還是 OOP。若 Hero 處於 **In Position (IP)**，請傾向於建議更寬的跟注 (Call) 或浮打 (Float) 範圍；若 **Out of Position (OOP)**，則建議更緊的防守。勿出現「CO vs UTG+1 是不利位置」等與系統事實矛盾的結論。**"""

    hand_content = hand_data.get("content", "")
    
    prompt = f"""你是 Hero 的專屬撲克教練 "Poker Copilot"。
你的風格是：**先同理心 (Empathy)，再講邏輯 (Logic)，最後給建議 (Action)**。
你要像一個在牌桌旁看了 20 年牌的老手，說話犀利但有溫度，不要像機器人一樣背誦公式。

【時間線裁決 (CRITICAL TIMELINE RULE)】
你正在覆盤 Hero 的「當下決策」。
1. **嚴禁偷看未來**：當 Hero 行動時，排在 Hero 後面的玩家尚未行動。即使 Log 顯示他們後來 Call 了，你在分析當下必須假定他們動作未知。
2. **位置檢核**：嚴格確認 Hero 相對位置，不要混淆順序。

【一致性協議 (Consistency Protocol)】
你的分析必須具備「重現性」。對於同一手牌數據，必須給出相同的建議。
- 當遇到「邊緣決策 (Close Call)」時，請優先選擇 **GTO 頻率最高** 的選項，而不是隨機挑選「混合策略 (Mixed Strategy)」中的小頻率選項。
- 除非有明確的剝削理由（例如對手數據異常），否則一律以**標準 GTO 線路**為準。

【陷阱牌過濾機制 (Trap Hand Filter)】
5. **非同花人頭牌 (Offsuit Broadways)**（如 JTo, QJo, KJo, ATo）：
   - 在面對 UTG/EP 加注時，這些牌通常是被壓制 (Dominated) 的。
   - 即使底池賠率 (Pot Odds) 很好，也要考慮 **反向隱含賠率 (Reverse Implied Odds)**。
   - **預設動作**：除非是在 BTN/BB 且對手極弱，否則面對早位加注，優先建議 **棄牌 (Fold)**。
   - 不要因為「便宜」就建議跟注。便宜的代價往往是翻後輸掉更大的底池。

【語氣範例 (Few-Shot Examples) - 請模仿這種說話方式】

範例 1 (Hero 正確棄掉陷阱牌):
"一句話狠評：別被賠率騙了，這手牌是典型的捕鼠籠。
===SPLIT===
### 🧐 局勢解讀
我知道你在 BTN 拿到 JTo，前面有三個人入池，底池賠率看起來香得不得了，只要付一點點就能看翻牌。
但兄弟，這就是標準的『反向隱含賠率』陷阱！
UTG 的開牌範圍裡全是 AJ, KJ, QJ, AT，你的牌天生被壓制。如果你中了 J 或 T，你很難贏大底池，但很容易輸掉整疊籌碼。

### 💡 教練建議
GTO 在這裡是非常明確的：面對早位強勢加注，JTo 這種雜色牌就是直接棄掉 (Fold)。
省下的這 2BB，就是你未來的利潤。好棄牌！"

範例 2 (Hero 在錯誤的時機詐唬):
"一句話狠評：時機不對，泡沫期不要用邊緣牌對抗深籌碼。
===SPLIT===
### 🧐 局勢解讀
我很欣賞你這裡想要操作的心態，在泡沫期想用 A5s 偷雞，這個 aggressive 的想法是好的。
可惜這個對手是全場 Chip Leader，他跟注的範圍太寬了。根據死錢計算，你這裡的棄牌率 (Fold Equity) 不足以支持這次詐唬。

### 💡 教練建議
這不是你的錯，是時機不對。如果是決賽桌，這手牌就是神操作，但現在我們需要的是生存。下次這種邊緣牌，面對深籌碼還是穩一點好。"

範例 3 (Hero 打得好):
"一句話狠評：漂亮！精準利用了對手範圍過寬的弱點。
===SPLIT===
### 🧐 局勢解讀
這就是我要看到的打法！雖然 KJs 在這裡不是最強的牌，但你精準地判斷出 BB 位防守範圍過寬。
這個 Check-Raise 直接打斷了對手的節奏，完美的利用了位置優勢。

### 💡 教練建議
這手牌沒什麼好挑剔的，邏輯清晰，執行果斷。保持這種狀態，決賽桌就在前面了。"

---

【真實手牌數據】
{fact_sheet}

【手牌紀錄】
{hand_content}

---

【輸出格式】
0. **撲克牌**：提到撲克牌時一律使用 Emoji（如 A♥️, T♠️, K♣️），嚴禁純文字代碼。
1. **一句話狠評**：(模仿上面的語氣，直接點出關鍵)
2. ===SPLIT===
3. **Markdown 分析**：(包含「🧐 局勢解讀」與「💡 教練建議」兩個區塊，請用口語化解釋 EV 與範圍，不要機械式背誦定律)
"""
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1}
    }
    try:
        resp = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
        raw_text = resp.json()['candidates'][0]['content']['parts'][0]['text']
        # 回傳原始文字，由呼叫端依 ===SPLIT=== 切分顯示
        return raw_text
    except Exception as e:
        return f"分析失敗: {str(e)}"

# --- 4. 主介面邏輯 ---

if not api_key:
    st.markdown("""
    <div style='background-color: #161B22; padding: 20px; border-radius: 10px; border-left: 5px solid #00FF99;'>
        👋 <b>歡迎來到戰情室！</b><br>
        這裡不是普通的覆盤工具，這是你的<b>戰術漏洞雷達</b>。<br>
        上傳 GGPoker 手牌紀錄，AI 將為你：<br>
        1. 🕵️‍♂️ <b>精準抓漏</b>：自動識別讓你輸錢的關鍵手牌。<br>
        2. 🦁 <b>教練狠評</b>：用職業視角檢視你的每一個 Decision。<br>
        3. 📊 <b>風格診斷</b>：分析你的 VPIP/PFR，找出長期盈利阻礙。
    </div>
    <br>
    """, unsafe_allow_html=True)
    st.info("👈 請先在左側輸入通關密碼才能使用。")
else:
    # session_state：一鍵試用 Demo 模式
    if "use_demo" not in st.session_state:
        st.session_state.use_demo = False

    uploaded_file = st.file_uploader("📂 上傳比賽紀錄 (.txt)", type=["txt"])

    if uploaded_file:
        content = load_content(uploaded_file)
        st.session_state.use_demo = False
    elif st.session_state.use_demo:
        content = DEMO_HANDS_TEXT
        st.sidebar.warning("🦁 目前正在展示 Demo 牌譜 (共36手)")
    else:
        content = None
    
    # 主畫面大按鈕 (當沒有內容時顯示)
    if content is None:
        st.markdown("---")
        st.markdown("### 👋 歡迎來到 Poker Copilot")
        st.markdown("這是一個使用 AI 幫你覆盤撲克比賽的工具。你可以上傳 GG Poker 的手牌紀錄，或是...")
        
        col_demo_btn, _ = st.columns([1, 2])
        with col_demo_btn:
            if st.button("🎲 我沒檔案，先載入範例試玩看看", type="primary", key="main_demo_btn"):
                st.session_state.use_demo = True
                st.rerun()

    if content:
        # 呼叫解析函數
        hands, hero_name = parse_hands(content)

        # 反轉為時間正序（最舊→最新），並為每手牌加上 display_index（與 UI 一致）
        hands.reverse()
        for idx, h in enumerate(hands, start=1):
            h["display_index"] = idx
        
        if not hands:
            st.error("❌ 無法解析手牌，請確認格式。")
        else:
            total_hands = len(hands)
            vpip_count = sum(1 for h in hands if h['vpip'])
            pfr_count = sum(1 for h in hands if h['pfr'])
            
            vpip = round((vpip_count / total_hands) * 100, 1) if total_hands > 0 else 0
            pfr = round((pfr_count / total_hands) * 100, 1) if total_hands > 0 else 0

            # --- 智慧抓漏邏輯 ---
            # 篩選條件：Hero 參與 (vpip) 且輸掉 (not is_winner)，依底池大小排序取前 3 手
            leak_hands = [h for h in hands if h.get("vpip") and not h.get("is_winner", False)]
            leak_hands.sort(key=lambda h: h.get("total_pot", 0) or h.get("pot_size", 0), reverse=True)
            leak_hands = leak_hands[:3]

            # --- 分頁顯示 (合併為 2 個分頁) ---
            tab1, tab2 = st.tabs(["📊 賽事儀表板", "🔍 手牌深度覆盤"])

            with tab1:
                # --- 關鍵失誤偵測 (置頂) ---
                st.markdown("### ⚠️ 關鍵失誤偵測 (Smart Leak Detector)")
                st.caption("系統自動標記了 3 手你輸掉的最大底池，建議優先檢討這些「傷口」。")

                if leak_hands:
                    cols = st.columns(3)
                    for i, hand in enumerate(leak_hands):
                        with cols[i]:
                            with st.container(border=True):
                                pot_val = hand.get("total_pot") or hand.get("pot_size", 0)
                                st.markdown(f"#### 💸 Pot: {pot_val:,}")
                                pos = hand.get("position", "Other")
                                cards = hand.get("hero_cards_emoji") or cards_to_emoji(hand.get("hero_cards"))
                                st.text(f"📍 {pos} | {cards}")

                                btn_key = f"leak_analyze_{hand.get('display_index')}_{hand.get('id', i)}"
                                if st.button("⚡️ 深度戰術解析", key=btn_key, type="primary", use_container_width=True):
                                    with st.spinner("AI 教練正在重看這手牌..."):
                                        analysis = analyze_specific_hand(hand, api_key, selected_model)
                                        st.success("分析完成！")
                                        parts = analysis.split("===SPLIT===")
                                        summary_text = parts[0].strip() if parts else ""
                                        detail_text = parts[1].strip() if len(parts) > 1 else ""
                                        with st.expander("查看教練狠評", expanded=True):
                                            if summary_text:
                                                st.info(summary_text, icon="🦁")
                                            if detail_text:
                                                st.markdown(detail_text)
                                            elif not summary_text:
                                                st.markdown(analysis)
                else:
                    st.info("恭喜！這場比賽你似乎沒有輸掉什麼大底池 (或者資料不足)。")

                st.divider()

                # 數據卡片區塊
                st.markdown("### 📊 關鍵數據")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("總手牌數", total_hands)
                c2.metric("VPIP", f"{vpip}%")
                c3.metric("PFR", f"{pfr}%")
                c4.metric("Hero ID", hero_name if hero_name else "Unknown")
                
                # 分隔線
                st.divider()
                
                # AI 賽事總結區塊 (原 Tab 2 內容)
                st.markdown("### 🧠 AI 賽事總結")
                if st.button("生成 AI 賽事總結", key="summary_btn"):
                    with st.spinner("AI 思考中..."):
                        advice = generate_match_summary(hands, vpip, pfr, api_key, selected_model)
                        st.markdown(advice)

            with tab2:
                # 手牌覆盤區塊 (優化版)
                st.markdown("### 🔍 手牌覆盤")
                col_list, col_detail = st.columns([1, 2])
                
                with col_list:
                    # 進階篩選區：多重條件取交集
                    with st.expander("🔍 進階手牌篩選 (點擊展開)", expanded=True):
                        filter_option = st.selectbox(
                            "主要篩選",
                            ["全部", "💥 VPIP", "🏆 獲勝", "💸 落敗", "🔥 大底池 (>20BB)"],
                            index=0,
                            key="hand_filter"
                        )
                        if filter_option == "全部":
                            base_hands = hands
                        elif filter_option == "💥 VPIP":
                            base_hands = [h for h in hands if h.get("vpip")]
                        elif filter_option == "🏆 獲勝":
                            base_hands = [h for h in hands if h.get("result") == "win"]
                        elif filter_option == "💸 落敗":
                            base_hands = [h for h in hands if h.get("result") == "loss"]
                        else:
                            bb_size_default = 1
                            base_hands = [h for h in hands if (h.get("bb_size") or bb_size_default) and (h.get("pot_size", 0) > 20 * (h.get("bb_size") or bb_size_default))]
                        
                        card_type_options = ["對子 (Pair)", "Ax 牌型", "人頭大牌 (Broadway)"]
                        selected_card_types = st.multiselect("牌型篩選", card_type_options, default=[], key="card_type_filter")
                        position_options = ["BTN", "SB", "BB", "UTG", "MP", "CO"]
                        selected_positions = st.multiselect("位置篩選", position_options, default=[], key="position_filter")
                        
                        filtered_hands = base_hands
                        if selected_card_types:
                            def match_card_type(h):
                                if "對子 (Pair)" in selected_card_types and h.get("is_pair"):
                                    return True
                                if "Ax 牌型" in selected_card_types and h.get("is_ax"):
                                    return True
                                if "人頭大牌 (Broadway)" in selected_card_types and h.get("is_broadway"):
                                    return True
                                return False
                            filtered_hands = [h for h in filtered_hands if match_card_type(h)]
                        if selected_positions:
                            filtered_hands = [h for h in filtered_hands if h.get("position_name") in selected_positions]
                    
                    if not filtered_hands:
                        st.info("此分類無手牌")
                        hand_data = hands[0] if hands else {}
                    else:
                        # Build dataframe: Hand #, Position, Hole Cards, Result (no Pot column)
                        result_label = {"win": "Win", "loss": "Loss", "fold": "Fold"}
                        rows = []
                        for h in filtered_hands:
                            rows.append({
                                "Hand #": h.get("display_index", 0),
                                "Position": h.get("position", "—"),
                                "Hole Cards": h.get("hero_cards_emoji") or cards_to_emoji(h.get("hero_cards")),
                                "Result": result_label.get(h.get("result"), "—"),
                            })
                        hand_df = pd.DataFrame(rows)
                        def highlight_loss(row):
                            if row.get("Result") == "Loss":
                                return ["background-color: rgba(255, 75, 75, 0.25)"] * len(row)
                            return [""] * len(row)
                        styled_df = hand_df.style.apply(highlight_loss, axis=1)
                        event = st.dataframe(
                            styled_df,
                            use_container_width=True,
                            hide_index=True,
                            on_select="rerun",
                            selection_mode="single-row",
                            key="hand_selection_df",
                        )
                        selected_rows = getattr(event.selection, "rows", []) or []
                        if selected_rows:
                            hand_data = filtered_hands[selected_rows[0]]
                        else:
                            hand_data = filtered_hands[0]
                
                with col_detail:
                    # --- 手牌紀錄時間軸 (取代原始文字) ---
                    st.markdown("### 📜 手牌紀錄")
                    render_hand_history_timeline(
                        hand_data.get("content", ""),
                        hero_name=hand_data.get("hero", "Hero"),
                    )
                    st.markdown("---")
                    # --- AI 分析區塊 ---
                    st.markdown("### 🤖 AI 教練分析")
                    sys_position = hand_data.get("position", "Other")
                    sys_cards = hand_data.get("hero_cards_emoji") or cards_to_emoji(hand_data.get("hero_cards"))
                    st.caption(f"📍 **系統判定**：位置 {sys_position} | 手牌 {sys_cards}")
                    analyze_clicked = st.button(f"立即分析這手牌", key="analyze_btn", use_container_width=True)

                    # --- 執行分析 ---
                    if analyze_clicked:
                        with st.spinner(random.choice(LOADING_TEXTS)):
                            analysis = analyze_specific_hand(hand_data, api_key, selected_model)
                            st.markdown("### 💡 AI 分析結果")
                            parts = analysis.split("===SPLIT===")
                            summary_text = parts[0].strip() if parts else ""
                            detail_text = parts[1].strip() if len(parts) > 1 else ""
                            if summary_text and detail_text:
                                st.info(summary_text, icon="🦁")
                                st.markdown(detail_text)
                            else:
                                st.markdown(analysis)
                    else:
                        st.info("👆 點擊上方按鈕，查看教練建議")