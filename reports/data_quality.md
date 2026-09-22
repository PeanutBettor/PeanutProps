# Data Quality Report — EPL passes attempted

Primary source: **fotmob**. Cross-check source: **premierleague**.  
Latest raw fetch in DB: 2026-09-22 21:45:30 UTC

## Provider definitions of "passes attempted"

- **fotmob**: Opta (Stats Perform) via FotMob: 'Accurate passes' total = all pass attempts (open play + set pieces incl. crosses, long balls, goal kicks and GK throws); value = successful passes. Verified equal to premierleague.com Opta total_pass.
- **premierleague**: Opta (Stats Perform) via premierleague.com: stat 'total_pass' = all pass attempts; 'accurate_pass' = successful passes. This is the league's official Opta feed.
- Both are Opta (Stats Perform) numbers. PrizePicks' settlement provider for soccer is NOT verified here — confirm on PrizePicks' official scoring-providers page before treating either feed as the settlement number.

## 1. Matches expected vs fetched

| season | fixtures | finished (expected) | fetched | postponed/cancelled/awarded |
|---|---|---|---|---|
| 2024-25 | 380 | 380 | 380 | 0 |
| 2025-26 | 380 | 380 | 380 | 0 |
| 2026-27 | 380 | 50 | 50 | 0 |

Finished matches with no player rows: **0**


Row counts (player_match, primary source; `appeared` excludes unused subs):

| season | rows | appeared | distinct players |
|---|---|---|---|
| 2024-25 | 15188 | 11567 | 685 |
| 2025-26 | 15189 | 11492 | 678 |
| 2026-27 | 1999 | 1538 | 502 |

## 2. NULL passes_attempted / minutes_played (with reason codes)

| season | null_reasons | appeared | rows |
|---|---|---|---|
| 2024-25 | minutes_played:unused_sub;passes_attempted:unused_sub;passes_completed:unused_sub;subbed_off_minute:unused_sub;subbed_on_minute:unused_sub | False | 3621 |
| 2025-26 | minutes_played:unused_sub;passes_attempted:unused_sub;passes_completed:unused_sub;subbed_off_minute:unused_sub;subbed_on_minute:unused_sub | False | 3697 |
| 2026-27 | minutes_played:unused_sub;passes_attempted:unused_sub;passes_completed:unused_sub;subbed_off_minute:unused_sub;subbed_on_minute:unused_sub | False | 461 |

Players who **appeared** but have NULL passes or minutes: **0**


## 3. minutes > 0 but passes_attempted = 0 (flag for review)

Count: **378**. Mostly late substitutes; anything with high minutes deserves a manual look.

| season | match_id | player | team | pos | started | min | on_min | red |
|---|---|---|---|---|---|---|---|---|
| 2025-26 | 4813605 | Nathan Collins | Brentford | DEF | False | 30 | 59 | False |
| 2024-25 | 4506508 | Darwin Núñez | Liverpool | FWD | False | 30 | 60 | False |
| 2025-26 | 4813388 | Wilson Isidor | Sunderland | FWD | False | 27 | 63 | False |
| 2025-26 | 4813575 | Enes Ünal | AFC Bournemouth | FWD | False | 26 | 64 | False |
| 2025-26 | 4813553 | Wilson Isidor | Sunderland | FWD | False | 22 | 68 | False |
| 2024-25 | 4506590 | Liam Delap | Ipswich Town | FWD | False | 19 | 71 | False |
| 2025-26 | 4813378 | Callum Wilson | West Ham United | FWD | False | 19 | 71 | False |
| 2025-26 | 4813631 | Igor Jesus | Nottingham Forest | FWD | False | 19 | 71 | False |
| 2024-25 | 4506281 | Beto | Everton | FWD | False | 18 | 72 | False |
| 2025-26 | 4813468 | Rodrigo Muniz | Fulham | FWD | False | 18 | 72 | False |
| 2024-25 | 4506430 | Ramón Sosa | Nottingham Forest | FWD | False | 18 | 72 | False |
| 2025-26 | 4813579 | Donyell Malen | Aston Villa | FWD | False | 17 | 73 | False |
| 2025-26 | 4813473 | Wilson Odobert | Tottenham Hotspur | FWD | False | 17 | 73 | False |
| 2024-25 | 4506622 | Rodrigo Gomes | Wolverhampton Wanderers | FWD | False | 17 | 73 | False |
| 2025-26 | 4813451 | Chris Wood | Nottingham Forest | FWD | False | 16 | 74 | False |
| 2025-26 | 4813589 | Lyle Foster | Burnley | FWD | False | 16 | 74 | False |
| 2026-27 | 5795369 | Tyrone Mings | Aston Villa | DEF | False | 16 | 74 | False |
| 2025-26 | 4813533 | Yoane Wissa | Newcastle United | FWD | False | 15 | 75 | False |
| 2025-26 | 4813622 | Benjamin Sesko | Manchester United | FWD | False | 15 | 75 | False |
| 2025-26 | 4813637 | Tosin Adarabioyo | Chelsea | DEF | False | 15 | 75 | False |
| 2025-26 | 4813681 | Daichi Kamada | Crystal Palace | MID | False | 15 | 75 | False |
| 2024-25 | 4506559 | Callum Wilson | Newcastle United | FWD | False | 13 | 77 | False |
| 2025-26 | 4813747 | Jean-Philippe Mateta | Crystal Palace | FWD | False | 13 | 77 | False |
| 2025-26 | 4813748 | Sean Neave | Newcastle United | FWD | False | 13 | 77 | False |
| 2026-27 | 5795437 | Promise David | Brighton & Hove Albion | FWD | False | 13 | 77 | False |
| 2024-25 | 4506521 | William Osula | Newcastle United | FWD | False | 12 | 78 | False |
| 2025-26 | 4813631 | Jean-Ricner Bellegarde | Wolverhampton Wanderers | MID | False | 12 | 78 | False |
| 2025-26 | 4813640 | William Osula | Newcastle United | FWD | False | 12 | 78 | False |
| 2024-25 | 4506387 | Niclas Füllkrug | West Ham United | FWD | False | 12 | 78 | False |
| 2024-25 | 4506389 | Callum Wilson | Newcastle United | FWD | False | 12 | 78 | False |
| 2025-26 | 4813541 | Callum Wilson | West Ham United | FWD | False | 11 | 79 | False |
| 2024-25 | 4506569 | Cameron Archer | Southampton | FWD | False | 11 | 79 | False |
| 2024-25 | 4506469 | Taiwo Awoniyi | Nottingham Forest | FWD | False | 11 | 79 | False |
| 2024-25 | 4506288 | Ian Maatsen | Aston Villa | DEF | False | 11 | 79 | False |
| 2025-26 | 4813639 | Beto | Everton | FWD | False | 11 | 79 | False |
| 2024-25 | 4506355 | Luis Díaz | Liverpool | FWD | False | 10 | 81 | False |
| 2025-26 | 4813606 | Tyler Dibling | Everton | FWD | False | 10 | 80 | False |
| 2024-25 | 4506453 | Ollie Watkins | Aston Villa | FWD | False | 10 | 80 | False |
| 2024-25 | 4506623 | Massimo Luongo | Ipswich Town | MID | False | 10 | 80 | False |
| 2024-25 | 4506362 | Santiago Bueno | Wolverhampton Wanderers | DEF | False | 10 | 80 | False |
| 2024-25 | 4506590 | Patson Daka | Leicester City | FWD | False | 10 | 80 | False |
| 2025-26 | 4813475 | Adam Smith | AFC Bournemouth | DEF | True | 10 |  | False |
| 2024-25 | 4506301 | Gabriel Jesus | Arsenal | FWD | False | 10 | 80 | False |
| 2025-26 | 4813505 | Enes Ünal | AFC Bournemouth | FWD | False | 10 | 80 | False |
| 2024-25 | 4506427 | Yankuba Minteh | Brighton & Hove Albion | FWD | False | 10 | 80 | False |
| 2025-26 | 4813534 | Callum Wilson | West Ham United | FWD | False | 9 | 81 | False |
| 2024-25 | 4506636 | Tim Iroegbunam | Everton | MID | False | 9 | 81 | False |
| 2024-25 | 4506465 | Wes Burns | Ipswich Town | FWD | False | 9 | 81 | False |
| 2024-25 | 4506519 | Oliver Scarles | West Ham United | DEF | False | 9 | 81 | False |
| 2024-25 | 4506618 | Yukinari Sugawara | Southampton | DEF | False | 9 | 81 | False |
| 2024-25 | 4506503 | Beto | Everton | FWD | False | 9 | 81 | False |
| 2025-26 | 4813713 | Callum Wilson | West Ham United | FWD | False | 9 | 81 | False |
| 2024-25 | 4506519 | Aaron Cresswell | West Ham United | DEF | False | 9 | 81 | False |
| 2025-26 | 4813517 | Tomás Soucek | West Ham United | MID | False | 8 | 82 | False |
| 2024-25 | 4506304 | Evan Ferguson | Brighton & Hove Albion | FWD | False | 8 | 82 | False |
| 2025-26 | 4813573 | Chris Rigg | Sunderland | MID | False | 8 | 82 | False |
| 2024-25 | 4506377 | Kenny Tete | Fulham | DEF | False | 8 | 82 | False |
| 2024-25 | 4506564 | Harrison Reed | Fulham | MID | False | 8 | 75 | False |
| 2026-27 | 5795427 | Valentín Barco | Chelsea | MID | False | 8 | 82 | False |
| 2024-25 | 4506367 | Santiago Bueno | Wolverhampton Wanderers | DEF | False | 8 | 82 | False |
| 2024-25 | 4506548 | Massimo Luongo | Ipswich Town | MID | False | 8 | 81 | False |
| 2025-26 | 4813500 | Noah Okafor | Leeds United | FWD | False | 8 | 82 | False |
| 2024-25 | 4506451 | Cameron Archer | Southampton | FWD | False | 8 | 82 | False |
| 2026-27 | 5795369 | Alysson Edward | Aston Villa | FWD | False | 8 | 82 | False |
| 2026-27 | 5795369 | Matteo Ruggeri | Aston Villa | DEF | False | 8 | 81 | False |
| 2024-25 | 4506279 | Ali Al Hamadi | Ipswich Town | FWD | False | 7 | 83 | False |
| 2025-26 | 4813560 | Jayden Bogle | Leeds United | MID | False | 7 | 83 | False |
| 2025-26 | 4813566 | Arnaud Kalimuendo-Muinga | Nottingham Forest | FWD | False | 7 | 84 | False |
| 2025-26 | 4813647 | Taiwo Awoniyi | Nottingham Forest | FWD | False | 7 | 83 | False |
| 2026-27 | 5795450 | Daniel James | Leeds United | MID | False | 7 | 83 | False |
| 2024-25 | 4506522 | Nathan Wood | Southampton | DEF | False | 7 | 83 | False |
| 2025-26 | 4813472 | Brian Brobbey | Sunderland | FWD | False | 7 | 83 | False |
| 2025-26 | 4813484 | Kyle Walker-Peters | West Ham United | DEF | False | 7 | 83 | False |
| 2025-26 | 4813388 | Joe Worrall | Burnley | DEF | False | 7 | 83 | False |
| 2025-26 | 4813424 | James Justin | Leeds United | DEF | False | 7 | 83 | False |
| 2025-26 | 4813566 | Donyell Malen | Aston Villa | FWD | False | 7 | 83 | False |
| 2024-25 | 4506446 | Christopher Nkunku | Chelsea | FWD | False | 7 | 83 | False |
| 2025-26 | 4813425 | Donyell Malen | Aston Villa | FWD | False | 7 | 83 | False |
| 2024-25 | 4506317 | James Garner | Everton | MID | False | 7 | 83 | False |
| 2024-25 | 4506362 | Albert Grønbæk | Southampton | MID | False | 7 | 83 | False |
| 2025-26 | 4813536 | Shea Lacey | Manchester United | FWD | False | 6 | 84 | False |
| 2025-26 | 4813609 | William Osula | Newcastle United | FWD | False | 6 | 84 | False |
| 2025-26 | 4813701 | Viktor Gyökeres | Arsenal | FWD | False | 6 | 84 | False |
| 2025-26 | 4813464 | Tolu Arokodare | Wolverhampton Wanderers | FWD | False | 6 | 84 | False |
| 2024-25 | 4506580 | Omar Marmoush | Manchester City | FWD | False | 6 | 84 | False |
| 2026-27 | 5795464 | Ibrahim Mbaye | Aston Villa | FWD | False | 6 | 84 | False |
| 2025-26 | 4813411 | Raul Jiménez | Fulham | FWD | False | 6 | 84 | False |
| 2024-25 | 4506472 | Nathaniel Clyne | Crystal Palace | MID | False | 6 | 84 | False |
| 2024-25 | 4506548 | Nathan Butler-Oyedeji | Arsenal | FWD | False | 6 | 84 | False |
| 2025-26 | 4813415 | William Osula | Newcastle United | FWD | False | 6 | 84 | False |
| 2025-26 | 4813375 | Donyell Malen | Aston Villa | FWD | False | 6 | 84 | False |
| 2025-26 | 4813381 | Justin Devenny | Crystal Palace | MID | False | 6 | 84 | False |
| 2024-25 | 4506268 | Philip Billing | AFC Bournemouth | MID | False | 6 | 84 | False |
| 2025-26 | 4813387 | Rico Henry | Brentford | DEF | False | 6 | 84 | False |
| 2025-26 | 4813501 | Joël Veltman | Brighton & Hove Albion | DEF | False | 6 | 84 | False |
| 2024-25 | 4506519 | Rodrigo Muniz | Fulham | FWD | False | 5 | 85 | False |
| 2025-26 | 4813562 | Beto | Everton | FWD | False | 5 | 85 | False |
| 2024-25 | 4506353 | Ben Mee | Brentford | DEF | False | 5 | 85 | False |
| 2025-26 | 4813449 | Kobbie Mainoo | Manchester United | MID | False | 5 | 85 | False |
| 2024-25 | 4506483 | David Brooks | AFC Bournemouth | FWD | False | 5 | 85 | False |
| 2025-26 | 4813569 | Federico Chiesa | Liverpool | FWD | False | 5 | 85 | False |
| 2025-26 | 4813587 | Josh Acheampong | Chelsea | DEF | False | 5 | 85 | False |
| 2025-26 | 4813589 | Josh Laurent | Burnley | MID | False | 5 | 85 | False |
| 2025-26 | 4813594 | Rodrigo Gomes | Wolverhampton Wanderers | MID | False | 5 | 86 | False |
| 2024-25 | 4506570 | Hee-Chan Hwang | Wolverhampton Wanderers | FWD | False | 5 | 85 | False |
| 2024-25 | 4506266 | Mason Holgate | Everton | DEF | False | 5 | 85 | False |
| 2025-26 | 4813399 | William Saliba | Arsenal | DEF | True | 5 |  | False |
| 2025-26 | 4813734 | Callum Wilson | West Ham United | FWD | False | 5 | 85 | False |
| 2025-26 | 4813737 | Ian Maatsen | Aston Villa | DEF | False | 5 | 85 | False |
| 2024-25 | 4506386 | Jaden Philogene-Bidace | Ipswich Town | FWD | False | 5 | 71 | False |
| 2024-25 | 4506273 | Daniel Jebbison | AFC Bournemouth | FWD | False | 5 | 85 | False |
| 2024-25 | 4506445 | Nathaniel Clyne | Crystal Palace | MID | False | 5 | 85 | False |
| 2024-25 | 4506499 | Patson Daka | Leicester City | FWD | False | 5 | 85 | False |
| 2024-25 | 4506552 | Ross Stewart | Southampton | FWD | False | 5 | 85 | False |
| 2024-25 | 4506335 | Ben White | Arsenal | DEF | False | 5 | 85 | False |
| 2025-26 | 4813493 | Anthony Elanga | Newcastle United | FWD | False | 5 | 85 | False |
| 2025-26 | 4813379 | Marcus Edwards | Burnley | MID | False | 5 | 85 | False |
| 2024-25 | 4506357 | Dane Scarlett | Tottenham Hotspur | FWD | False | 4 | 86 | False |
| 2024-25 | 4506372 | Youssef Chermiti | Everton | FWD | False | 4 | 86 | False |
| 2025-26 | 4813463 | William Osula | Newcastle United | FWD | False | 4 | 86 | False |
| 2025-26 | 4813615 | Adam Smith | AFC Bournemouth | DEF | False | 4 | 86 | False |
| 2025-26 | 4813646 | Alejandro Garnacho | Chelsea | FWD | False | 4 | 86 | False |
| 2025-26 | 4813457 | Donyell Malen | Aston Villa | FWD | False | 4 | 86 | False |
| 2026-27 | 5795369 | Alejandro Garnacho | Aston Villa | FWD | False | 4 | 86 | False |
| 2026-27 | 5795425 | Tim Iroegbunam | Everton | MID | False | 4 | 87 | False |
| 2026-27 | 5795436 | Callum Wilson | Brentford | FWD | False | 4 | 86 | False |
| 2024-25 | 4506481 | Jack Harrison | Everton | FWD | False | 4 | 86 | False |
| 2024-25 | 4506602 | Santiago Bueno | Wolverhampton Wanderers | DEF | False | 4 | 87 | False |
| 2024-25 | 4506593 | Jake Evans | Leicester City | FWD | False | 4 | 86 | False |
| 2024-25 | 4506599 | Kiernan Dewsbury-Hall | Chelsea | MID | False | 4 | 86 | False |
| 2025-26 | 4813408 | Joe Worrall | Burnley | DEF | False | 4 | 86 | False |
| 2025-26 | 4813457 | Ian Maatsen | Aston Villa | DEF | False | 4 | 86 | False |
| 2024-25 | 4506273 | Adam Smith | AFC Bournemouth | DEF | False | 4 | 86 | False |
| 2024-25 | 4506555 | Vladimír Coufal | West Ham United | DEF | False | 4 | 86 | False |
| 2025-26 | 4813653 | William Osula | Newcastle United | FWD | False | 4 | 86 | False |
| 2024-25 | 4506372 | Cody Gakpo | Liverpool | FWD | False | 4 | 86 | False |
| 2025-26 | 4813647 | Solly March | Brighton & Hove Albion | FWD | False | 4 | 86 | False |
| 2025-26 | 4813552 | Taiwo Awoniyi | Nottingham Forest | FWD | False | 3 | 87 | False |
| 2025-26 | 4813461 | Daniel James | Leeds United | FWD | False | 3 | 87 | False |
| 2024-25 | 4506376 | Dwight McNeil | Everton | FWD | False | 3 | 87 | False |
| 2025-26 | 4813391 | Ayden Heaven | Manchester United | DEF | False | 3 | 87 | False |
| 2024-25 | 4506415 | Kamaldeen Sulemana | Southampton | MID | False | 3 | 87 | False |
| 2025-26 | 4813676 | Tammy Abraham | Aston Villa | FWD | False | 3 | 87 | False |
| 2025-26 | 4813692 | Tammy Abraham | Aston Villa | FWD | False | 3 | 87 | False |
| 2024-25 | 4506641 | Callum Wilson | Newcastle United | FWD | False | 3 | 87 | False |
| 2025-26 | 4813405 | Jack Hinshelwood | Brighton & Hove Albion | MID | True | 3 |  | False |
| 2024-25 | 4506287 | Harrison Reed | Fulham | MID | False | 3 | 87 | False |
| 2024-25 | 4506537 | Matt Doherty | Wolverhampton Wanderers | DEF | False | 3 | 87 | False |
| 2024-25 | 4506431 | Callum Wilson | Newcastle United | FWD | False | 3 | 87 | False |
| 2024-25 | 4506447 | Adama Traoré | Fulham | FWD | False | 3 | 87 | False |
| 2024-25 | 4506620 | William Osula | Newcastle United | FWD | False | 3 | 87 | False |
| 2025-26 | 4813479 | Emile Smith Rowe | Fulham | MID | False | 3 | 87 | False |
| 2025-26 | 4813482 | Eliezer Mayenda | Sunderland | FWD | False | 3 | 87 | False |
| 2025-26 | 4813580 | Nathan Patterson | Everton | DEF | False | 3 | 87 | False |
| 2024-25 | 4506349 | Morato | Nottingham Forest | DEF | False | 3 | 87 | False |
| 2025-26 | 4813503 | Timothy Castagne | Fulham | DEF | False | 3 | 87 | False |
| 2024-25 | 4506509 | Danny Ings | West Ham United | FWD | False | 3 | 87 | False |
| 2025-26 | 4813508 | Jaydee Canvot | Crystal Palace | DEF | False | 2 | 88 | False |
| 2025-26 | 4813523 | Keane Lewis-Potter | Brentford | DEF | False | 2 | 88 | False |
| 2024-25 | 4506321 | Issa Diop | Fulham | DEF | False | 2 | 88 | False |
| 2025-26 | 4813389 | Odsonne Édouard | Crystal Palace | FWD | False | 2 | 88 | False |
| 2025-26 | 4813547 | Zian Flemming | Burnley | FWD | False | 2 | 88 | False |
| 2025-26 | 4813557 | Ashley Barnes | Burnley | FWD | False | 2 | 88 | False |
| 2025-26 | 4813572 | Joseph Willock | Newcastle United | MID | False | 2 | 88 | False |
| 2025-26 | 4813588 | Jonah Kusi-Asare | Fulham | FWD | False | 2 | 88 | False |
| 2025-26 | 4813596 | Noussair Mazraoui | Manchester United | DEF | False | 2 | 88 | False |
| 2025-26 | 4813633 | William Osula | Newcastle United | FWD | False | 2 | 88 | False |
| 2025-26 | 4813667 | Lesley Ugochukwu | Burnley | MID | False | 2 | 88 | False |
| 2025-26 | 4813697 | Roméo Lavia | Chelsea | MID | False | 2 | 88 | False |
| 2025-26 | 4813723 | Lewis Dunk | Brighton & Hove Albion | DEF | False | 2 | 88 | False |
| 2024-25 | 4506442 | Jean-Clair Todibo | West Ham United | DEF | False | 2 | 88 | False |
| 2024-25 | 4506634 | Carlos Soler | West Ham United | MID | False | 2 | 88 | False |
| 2024-25 | 4506642 | Albert Grønbæk | Southampton | MID | False | 2 | 88 | False |
| 2024-25 | 4506466 | Evan Ferguson | Brighton & Hove Albion | FWD | False | 2 | 88 | False |
| 2024-25 | 4506442 | Aaron Cresswell | West Ham United | DEF | False | 2 | 88 | False |
| 2024-25 | 4506475 | Christopher Nkunku | Chelsea | FWD | False | 2 | 88 | False |
| 2025-26 | 4813412 | Nathan Aké | Manchester City | DEF | False | 2 | 88 | False |
| 2024-25 | 4506619 | Nathaniel Clyne | Crystal Palace | MID | False | 2 | 88 | False |
| 2024-25 | 4506378 | Santiago Bueno | Wolverhampton Wanderers | DEF | False | 2 | 88 | False |
| 2024-25 | 4506411 | Kamaldeen Sulemana | Southampton | MID | False | 2 | 88 | False |
| 2025-26 | 4813404 | Charly Alcaraz | Everton | MID | False | 2 | 88 | False |
| 2024-25 | 4506620 | Issa Diop | Fulham | DEF | False | 2 | 88 | False |
| 2024-25 | 4506274 | Reiss Nelson | Arsenal | FWD | False | 2 | 88 | False |
| 2025-26 | 4813561 | Fer López | Wolverhampton Wanderers | MID | False | 2 | 88 | False |
| 2024-25 | 4506276 | Jean-Clair Todibo | West Ham United | DEF | False | 2 | 88 | False |
| 2024-25 | 4506478 | Odsonne Édouard | Leicester City | FWD | False | 2 | 88 | False |
| 2025-26 | 4813377 | Aaron Hickey | Brentford | DEF | False | 2 | 88 | False |
| 2025-26 | 4813465 | Charalampos Kostoulas | Brighton & Hove Albion | FWD | False | 2 | 88 | False |
| 2024-25 | 4506512 | Taiwo Awoniyi | Nottingham Forest | FWD | False | 2 | 88 | False |
| 2024-25 | 4506431 | Joseph Willock | Newcastle United | MID | False | 2 | 88 | False |
| 2024-25 | 4506263 | Jay Stansfield | Fulham | MID | False | 1 | 90 | False |
| 2025-26 | 4813509 | Nathan Aké | Manchester City | DEF | False | 1 | 90 | False |
| 2025-26 | 4813429 | Igor Julio | West Ham United | DEF | False | 1 | 90 | False |
| 2025-26 | 4813511 | Luke O'Nien | Sunderland | DEF | False | 1 | 90 | False |
| 2025-26 | 4813522 | Sandro Tonali | Newcastle United | MID | False | 1 | 90 | False |
| 2025-26 | 4813437 | Ian Maatsen | Aston Villa | DEF | False | 1 | 90 | False |
| 2024-25 | 4506453 | Emiliano Buendía | Aston Villa | FWD | False | 1 | 90 | False |
| 2025-26 | 4813440 | Séamus Coleman | Everton | MID | False | 1 | 90 | False |
| 2024-25 | 4506434 | Edmond-Paris Maghoma | Brentford | MID | False | 1 | 90 | False |
| 2025-26 | 4813526 | Jack Harrison | Leeds United | FWD | False | 1 | 90 | False |
| 2025-26 | 4813535 | Amine Adli | AFC Bournemouth | FWD | False | 1 | 90 | False |
| 2024-25 | 4506469 | Eric da Silva Moreira | Nottingham Forest | DEF | False | 1 | 89 | False |
| 2025-26 | 4813543 | Andrew Robertson | Liverpool | DEF | False | 1 | 90 | False |
| 2024-25 | 4506479 | William Osula | Newcastle United | FWD | False | 1 | 90 | False |
| 2025-26 | 4813444 | Tolu Arokodare | Wolverhampton Wanderers | FWD | False | 1 | 90 | False |
| 2025-26 | 4813546 | Reiss Nelson | Brentford | FWD | False | 1 | 89 | False |
| 2024-25 | 4506459 | Carlos Forbs | Wolverhampton Wanderers | FWD | False | 1 | 89 | False |
| 2024-25 | 4506362 | Nasser Djiga | Wolverhampton Wanderers | DEF | False | 1 | 90 | False |
| 2025-26 | 4813452 | Daniel Neil | Sunderland | MID | False | 1 | 90 | False |
| 2025-26 | 4813558 | Adam Smith | AFC Bournemouth | DEF | False | 1 | 90 | False |
| 2024-25 | 4506331 | Matheus Nunes | Manchester City | DEF | False | 1 | 89 | False |
| 2025-26 | 4813561 | David Møller Wolfe | Wolverhampton Wanderers | DEF | False | 1 | 90 | False |
| 2025-26 | 4813559 | Borna Sosa | Crystal Palace | MID | False | 1 | 90 | False |
| 2024-25 | 4506518 | Álex Moreno | Nottingham Forest | DEF | False | 1 | 90 | False |
| 2024-25 | 4506406 | Rodrigo Gomes | Wolverhampton Wanderers | FWD | False | 1 | 90 | False |
| 2025-26 | 4813568 | Myles Peart-Harris | Brentford | FWD | False | 1 | 90 | False |
| 2024-25 | 4506367 | Boubacar Traoré | Wolverhampton Wanderers | MID | False | 1 | 90 | False |
| 2024-25 | 4506363 | Jaden Philogene-Bidace | Ipswich Town | FWD | False | 1 | 90 | False |
| 2024-25 | 4506370 | Lewis Miley | Newcastle United | MID | False | 1 | 90 | False |
| 2025-26 | 4813575 | Veljko Milosavljevic | AFC Bournemouth | DEF | False | 1 | 90 | False |
| 2024-25 | 4506290 | Miguel Almirón | Newcastle United | FWD | False | 1 | 90 | False |
| 2025-26 | 4813580 | Merlin Röhl | Everton | FWD | False | 1 | 90 | False |
| 2025-26 | 4813583 | Wilfried Gnonto | Leeds United | FWD | False | 1 | 90 | False |
| 2025-26 | 4813576 | Joseph Gomez | Liverpool | DEF | False | 1 | 90 | False |
| 2025-26 | 4813590 | Mason Mount | Manchester United | MID | False | 1 | 90 | False |
| 2024-25 | 4506371 | Yukinari Sugawara | Southampton | DEF | False | 1 | 89 | False |
| 2025-26 | 4813390 | Harrison Armstrong | Everton | MID | False | 1 | 90 | False |
| 2024-25 | 4506562 | Gonçalo Guedes | Wolverhampton Wanderers | FWD | False | 1 | 89 | False |
| 2025-26 | 4813593 | Max Kilman | West Ham United | DEF | False | 1 | 90 | False |
| 2025-26 | 4813393 | Wataru Endo | Liverpool | MID | False | 1 | 90 | False |
| 2025-26 | 4813604 | Max Kilman | West Ham United | DEF | False | 1 | 90 | False |
| 2024-25 | 4506378 | Nasser Djiga | Wolverhampton Wanderers | DEF | False | 1 | 90 | False |
| 2025-26 | 4813600 | Beto | Everton | FWD | False | 1 | 89 | False |
| 2024-25 | 4506480 | Massimo Luongo | Ipswich Town | MID | False | 1 | 90 | False |
| 2025-26 | 4813614 | Bafodé Diakité | AFC Bournemouth | DEF | False | 1 | 90 | False |
| 2024-25 | 4506441 | Joao Félix | Chelsea | FWD | False | 1 | 90 | False |
| 2024-25 | 4506486 | Ryan Sessegnon | Fulham | DEF | False | 1 | 90 | False |
| 2025-26 | 4813610 | Leny Yoro | Manchester United | DEF | False | 1 | 90 | False |
| 2025-26 | 4813613 | Omar Marmoush | Manchester City | FWD | False | 1 | 90 | False |
| 2025-26 | 4813620 | Sebastiaan Bornauw | Leeds United | DEF | False | 1 | 90 | False |
| 2024-25 | 4506318 | George Hirst | Ipswich Town | FWD | False | 1 | 90 | False |
| 2024-25 | 4506492 | Jean-Ricner Bellegarde | Wolverhampton Wanderers | MID | False | 1 | 90 | False |
| 2025-26 | 4813616 | Christian Nørgaard | Arsenal | MID | False | 1 | 89 | False |
| 2025-26 | 4813619 | Tim Iroegbunam | Everton | MID | False | 1 | 90 | False |
| 2025-26 | 4813621 | Nathan Aké | Manchester City | DEF | False | 1 | 90 | False |
| 2025-26 | 4813627 | Sean Longstaff | Leeds United | MID | False | 1 | 90 | False |
| 2025-26 | 4813458 | Frank Onyeka | Brentford | MID | False | 1 | 90 | False |
| 2025-26 | 4813404 | Séamus Coleman | Everton | MID | False | 1 | 90 | False |
| 2025-26 | 4813632 | Wilson Isidor | Sunderland | FWD | False | 1 | 90 | False |
| 2025-26 | 4813636 | Carlos Baleba | Brighton & Hove Albion | MID | False | 1 | 90 | False |
| 2024-25 | 4506313 | Luis Sinisterra | AFC Bournemouth | FWD | False | 1 | 89 | False |
| 2024-25 | 4506407 | William Osula | Newcastle United | FWD | False | 1 | 89 | False |
| 2025-26 | 4813639 | Ayden Heaven | Manchester United | DEF | False | 1 | 90 | False |
| 2025-26 | 4813653 | Michael Keane | Everton | DEF | False | 1 | 89 | False |
| 2024-25 | 4506516 | Jakub Moder | Brighton & Hove Albion | MID | False | 1 | 90 | False |
| 2024-25 | 4506472 | Jeffrey Schlupp | Crystal Palace | MID | False | 1 | 90 | False |
| 2025-26 | 4813661 | Morato | Nottingham Forest | DEF | False | 1 | 90 | False |
| 2025-26 | 4813662 | Sven Botman | Newcastle United | DEF | False | 1 | 90 | False |
| 2025-26 | 4813455 | Arnaud Kalimuendo-Muinga | Nottingham Forest | FWD | False | 1 | 89 | False |
| 2025-26 | 4813673 | Matthew O'Riley | Brighton & Hove Albion | MID | False | 1 | 90 | False |
| 2025-26 | 4813665 | Tyrique George | Everton | FWD | False | 1 | 90 | False |
| 2025-26 | 4813670 | James Rowswell | Tottenham Hotspur | DEF | False | 1 | 90 | False |
| 2025-26 | 4813678 | Tim Iroegbunam | Everton | MID | False | 1 | 89 | False |
| 2025-26 | 4813682 | Eliezer Mayenda | Sunderland | FWD | False | 1 | 90 | False |
| 2025-26 | 4813396 | Diego Coppola | Brighton & Hove Albion | DEF | False | 1 | 90 | False |
| 2025-26 | 4813685 | Enes Ünal | AFC Bournemouth | FWD | False | 1 | 90 | False |
| 2025-26 | 4813689 | Yoane Wissa | Newcastle United | FWD | False | 1 | 90 | False |
| 2024-25 | 4506385 | Jake Evans | Leicester City | FWD | False | 1 | 90 | False |
| 2025-26 | 4813456 | Christantus Uche | Crystal Palace | FWD | False | 1 | 90 | False |
| 2024-25 | 4506633 | Daniel Jebbison | AFC Bournemouth | FWD | False | 1 | 89 | False |
| 2025-26 | 4813713 | Jean-Clair Todibo | West Ham United | DEF | False | 1 | 90 | False |
| 2025-26 | 4813714 | David Møller Wolfe | Wolverhampton Wanderers | DEF | False | 1 | 90 | False |
| 2025-26 | 4813721 | Daniel James | Leeds United | FWD | False | 1 | 90 | False |
| 2025-26 | 4813718 | Kaye Furo | Brentford | FWD | False | 1 | 90 | False |
| 2024-25 | 4506572 | Sven Botman | Newcastle United | DEF | False | 1 | 90 | False |
| 2025-26 | 4813724 | Tom Edozie | Wolverhampton Wanderers | MID | False | 1 | 90 | False |
| 2025-26 | 4813722 | Leny Yoro | Manchester United | DEF | False | 1 | 90 | False |
| 2025-26 | 4813717 | Pape Sarr | Tottenham Hotspur | MID | False | 1 | 90 | False |
| 2025-26 | 4813720 | Harrison Armstrong | Everton | MID | False | 1 | 90 | False |
| 2025-26 | 4813732 | Eliezer Mayenda | Sunderland | FWD | False | 1 | 90 | False |
| 2025-26 | 4813727 | Charly Alcaraz | Everton | MID | False | 1 | 90 | False |
| 2024-25 | 4506384 | Gustavo Nunes | Brentford | FWD | False | 1 | 90 | False |
| 2024-25 | 4506325 | Mads Roerslev | Brentford | DEF | False | 1 | 90 | False |
| 2025-26 | 4813460 | Mathys Tel | Tottenham Hotspur | FWD | False | 1 | 90 | False |
| 2024-25 | 4506398 | William Osula | Newcastle United | FWD | False | 1 | 90 | False |
| 2024-25 | 4506402 | Jean-Ricner Bellegarde | Wolverhampton Wanderers | MID | False | 1 | 90 | False |
| 2025-26 | 4813754 | Sebastiaan Bornauw | Leeds United | DEF | False | 1 | 90 | False |
| 2026-27 | 5795367 | Arnaud Kalimuendo-Muinga | Nottingham Forest | FWD | False | 1 | 90 | False |
| 2025-26 | 4813465 | Nehemiah Oriola | Brighton & Hove Albion | FWD | False | 1 | 90 | False |
| 2026-27 | 5795371 | Fabian Schär | Newcastle United | DEF | False | 1 | 90 | False |
| 2024-25 | 4506573 | Ian Maatsen | Aston Villa | DEF | False | 1 | 89 | False |
| 2024-25 | 4506487 | Memeh Caleb Okoli | Leicester City | DEF | False | 1 | 90 | False |
| 2026-27 | 5795441 | Lewis Koumas | Liverpool | FWD | False | 1 | 90 | False |
| 2026-27 | 5795443 | Daniel Jebbison | AFC Bournemouth | FWD | False | 1 | 89 | False |
| 2024-25 | 4506592 | Jota Silva | Nottingham Forest | FWD | False | 1 | 90 | False |
| 2024-25 | 4506405 | Conor Townsend | Ipswich Town | DEF | False | 1 | 90 | False |
| 2026-27 | 5795446 | Chris Wood | Nottingham Forest | FWD | False | 1 | 90 | False |
| 2024-25 | 4506530 | Remy Rees-Dottin | AFC Bournemouth | MID | False | 1 | 90 | False |
| 2025-26 | 4813409 | Chris Rigg | Sunderland | MID | False | 1 | 90 | False |
| 2026-27 | 5795463 | Joel Latibeaudiere | Coventry City | DEF | False | 1 | 90 | False |
| 2025-26 | 4813466 | Myles Lewis-Skelly | Arsenal | DEF | False | 1 | 90 | False |
| 2024-25 | 4506314 | Abdul Fatawu | Leicester City | FWD | False | 1 | 90 | False |
| 2024-25 | 4506415 | John Stones | Manchester City | DEF | False | 1 | 90 | False |
| 2024-25 | 4506334 | Solly March | Brighton & Hove Albion | FWD | False | 1 | 90 | False |
| 2024-25 | 4506340 | Welington | Southampton | DEF | False | 1 | 89 | False |
| 2025-26 | 4813413 | Sven Botman | Newcastle United | DEF | False | 1 | 90 | False |
| 2024-25 | 4506430 | James McAtee | Manchester City | MID | False | 1 | 90 | False |
| 2025-26 | 4813414 | Andy Irving | West Ham United | MID | False | 1 | 90 | False |
| 2024-25 | 4506482 | Matt Doherty | Wolverhampton Wanderers | DEF | False | 1 | 90 | False |
| 2024-25 | 4506544 | Gustavo Nunes | Brentford | FWD | False | 1 | 90 | False |
| 2025-26 | 4813471 | Ibrahim Sangaré | Nottingham Forest | MID | False | 1 | 90 | False |
| 2024-25 | 4506459 | Jean-Ricner Bellegarde | Wolverhampton Wanderers | MID | False | 1 | 89 | False |
| 2025-26 | 4813408 | Armando Broja | Burnley | FWD | False | 1 | 89 | False |
| 2024-25 | 4506530 | Ben Winterburn | AFC Bournemouth | MID | False | 1 | 90 | False |
| 2024-25 | 4506618 | George Hirst | Ipswich Town | FWD | False | 1 | 89 | False |
| 2024-25 | 4506299 | Matheus Nunes | Manchester City | DEF | False | 1 | 90 | False |
| 2024-25 | 4506606 | Ben Mee | Brentford | DEF | False | 1 | 90 | False |
| 2024-25 | 4506539 | Kiernan Dewsbury-Hall | Chelsea | MID | False | 1 | 90 | False |
| 2024-25 | 4506340 | Shumaira Mheuka | Chelsea | FWD | False | 1 | 90 | False |
| 2024-25 | 4506336 | Jack Grealish | Manchester City | FWD | False | 1 | 90 | False |
| 2024-25 | 4506356 | Guido Rodríguez | West Ham United | MID | False | 1 | 90 | False |
| 2024-25 | 4506537 | Gonçalo Guedes | Wolverhampton Wanderers | FWD | False | 1 | 90 | False |
| 2024-25 | 4506342 | Victor Nilsson Lindelöf | Manchester United | DEF | False | 1 | 90 | False |
| 2024-25 | 4506372 | Wataru Endo | Liverpool | DEF | False | 1 | 90 | False |
| 2025-26 | 4813424 | Lukas Nmecha | Leeds United | FWD | False | 1 | 90 | False |
| 2024-25 | 4506495 | Edward Nketiah | Crystal Palace | MID | False | 1 | 90 | False |
| 2024-25 | 4506570 | Nico González | Manchester City | MID | False | 1 | 90 | False |
| 2024-25 | 4506569 | Michael Golding | Leicester City | MID | False | 1 | 90 | False |
| 2024-25 | 4506572 | Emil Krafth | Newcastle United | DEF | False | 1 | 90 | False |
| 2024-25 | 4506580 | William Smallbone | Southampton | MID | False | 1 | 90 | False |
| 2024-25 | 4506611 | Will Lankshear | Tottenham Hotspur | FWD | False | 1 | 90 | False |
| 2024-25 | 4506593 | Ben Winterburn | AFC Bournemouth | MID | False | 1 | 90 | False |
| 2024-25 | 4506602 | Tom King | Wolverhampton Wanderers | GK | False | 1 | 90 | False |
| 2025-26 | 4813378 | Chris Rigg | Sunderland | MID | False | 1 | 90 | False |
| 2024-25 | 4506445 | Justin Devenny | Crystal Palace | MID | False | 1 | 90 | False |
| 2024-25 | 4506550 | Nasser Djiga | Wolverhampton Wanderers | DEF | False | 1 | 90 | False |
| 2025-26 | 4813405 | Julio Soler | AFC Bournemouth | DEF | False | 1 | 90 | False |
| 2024-25 | 4506336 | Ilkay Gündogan | Manchester City | MID | False | 1 | 90 | False |
| 2024-25 | 4506420 | Will Lankshear | Tottenham Hotspur | FWD | False | 1 | 90 | False |
| 2025-26 | 4813458 | Rico Henry | Brentford | DEF | False | 1 | 90 | False |
| 2025-26 | 4813455 | Enes Ünal | AFC Bournemouth | FWD | False | 1 | 90 | False |
| 2025-26 | 4813487 | Joël Veltman | Brighton & Hove Albion | DEF | False | 1 | 89 | False |
| 2025-26 | 4813465 | Joe Knight | Brighton & Hove Albion | MID | False | 1 | 90 | False |
| 2025-26 | 4813489 | Timothy Castagne | Fulham | DEF | False | 1 | 90 | False |
| 2025-26 | 4813500 | Omar Marmoush | Manchester City | FWD | False | 1 | 89 | False |
| 2025-26 | 4813526 | James Justin | Leeds United | DEF | False | 1 | 89 | False |
| 2025-26 | 4813543 | Federico Chiesa | Liverpool | FWD | False | 1 | 90 | False |
| 2025-26 | 4813489 | Eliezer Mayenda | Sunderland | FWD | False | 1 | 90 | False |
| 2024-25 | 4506291 | Taiwo Awoniyi | Nottingham Forest | FWD | False | 1 | 90 | False |
| 2024-25 | 4506558 | Manuel Akanji | Manchester City | DEF | False | 1 | 90 | False |
| 2025-26 | 4813422 | Daniel Neil | Sunderland | MID | False | 1 | 90 | False |
| 2025-26 | 4813583 | Sebastiaan Bornauw | Leeds United | DEF | False | 1 | 90 | False |
| 2025-26 | 4813590 | Ayden Heaven | Manchester United | DEF | False | 1 | 90 | False |
| 2025-26 | 4813588 | Sebastiaan Bornauw | Leeds United | DEF | False | 1 | 90 | False |
| 2024-25 | 4506314 | Odsonne Édouard | Leicester City | FWD | False | 1 | 90 | False |
| 2025-26 | 4813434 | Toti Gomes | Wolverhampton Wanderers | DEF | False | 1 | 90 | False |
| 2024-25 | 4506619 | Justin Devenny | Crystal Palace | MID | False | 1 | 90 | False |
| 2024-25 | 4506623 | Jack Taylor | Ipswich Town | MID | False | 1 | 90 | False |
| 2025-26 | 4813647 | Maxim De Cuyper | Brighton & Hove Albion | DEF | False | 1 | 90 | False |
| 2025-26 | 4813673 | Joël Veltman | Brighton & Hove Albion | DEF | False | 1 | 90 | False |
| 2025-26 | 4813682 | Reinildo | Sunderland | DEF | False | 1 | 90 | False |
| 2025-26 | 4813685 | Adam Smith | AFC Bournemouth | DEF | False | 1 | 90 | False |
| 2025-26 | 4813692 | Dan Ndoye | Nottingham Forest | FWD | False | 1 | 89 | False |
| 2025-26 | 4813701 | Nathan Aké | Manchester City | DEF | False | 1 | 90 | False |
| 2025-26 | 4813432 | Harvey Barnes | Newcastle United | FWD | False | 1 | 90 | False |
| 2024-25 | 4506343 | Donyell Malen | Aston Villa | FWD | False | 1 | 90 | False |
| 2024-25 | 4506314 | Gabriel Jesus | Arsenal | FWD | False | 1 | 90 | False |
| 2024-25 | 4506443 | Kaelan Casey | West Ham United | DEF | False | 1 | 90 | False |
| 2024-25 | 4506362 | Jack Stephens | Southampton | DEF | False | 1 | 90 | False |
| 2024-25 | 4506352 | Ashley Young | Everton | DEF | False | 1 | 90 | False |
| 2024-25 | 4506572 | Brajan Gruda | Brighton & Hove Albion | FWD | False | 1 | 90 | False |
| 2024-25 | 4506593 | Julio Soler | AFC Bournemouth | DEF | False | 1 | 90 | False |
| 2025-26 | 4813498 | Kobbie Mainoo | Manchester United | MID | False | 1 | 90 | False |
| 2024-25 | 4506632 | Fábio Carvalho | Brentford | MID | False | 1 | 90 | False |
| 2025-26 | 4813692 | Ryan Yates | Nottingham Forest | MID | False | 1 | 89 | False |
| 2024-25 | 4506356 | Evan Ferguson | West Ham United | FWD | False | 1 | 90 | False |
| 2024-25 | 4506631 | Chido Obi | Manchester United | FWD | False | 1 | 90 | False |
| 2024-25 | 4506593 | Alex Scott | AFC Bournemouth | MID | False | 1 | 90 | False |

## 4. Team totals sanity check

Team-matches: **1620**; min 168, median 436, max 819, mean 442.0.

Flagged (< 200 or > 900): **5**

| season | match_id | team | sum passes_att | appeared rows w/ NULL |
|---|---|---|---|---|
| 2024-25 | 4506267 | Newcastle United | 181 | 0 |
| 2025-26 | 4813387 | Brentford | 178 | 0 |
| 2024-25 | 4506376 | Everton | 189 | 0 |
| 2024-25 | 4506559 | Ipswich Town | 185 | 0 |
| 2025-26 | 4813408 | Burnley | 168 | 0 |

Sum of player passes vs FotMob's own team "Passes" stat (from cached raw):
checked **1620** team-matches, mismatches **0**, team stat unavailable **0**.


## 5. Cross-check vs premierleague.com (Opta)

Matches compared: **24**; player rows: **731**; both sources have a value: **718**; exact passes_attempted match: **718** (**100.00%**); mean absolute difference: **0.000**.  
Minutes agree exactly on 725/727 rows (reported for information; FotMob and the PL feed round stoppage time differently).

| outcome | join_method | rows |
|---|---|---|
| exact | opta_id | 538 |
| exact | name_exact | 177 |
| null_in_one | opta_id | 7 |
| exact | name_lastname | 3 |
| null_in_one | name_exact | 2 |
| missing_in_other | opta_id | 2 |
| missing_in_primary | unresolved | 2 |

Join: Opta player id. The PL feed omits Opta ids for some 2024-25 fixtures, so those rows fall back to an exact accent-insensitive name match (same side), then a unique last-name match. Names that still don't match are left unmatched (`unresolved`), not guessed. `null_in_one` means one source has the stat and the other doesn't. The PL feed drops zero-valued stats, so FotMob `0` vs PL absent is expected there.

Disagreements > 3 passes: **0**

Rows present in only one source or NULL in one:

| fotmob match | PL fixture | player | team | outcome | join | fotmob | PL | fotmob min | PL min |
|---|---|---|---|---|---|---|---|---|---|
| 4506323 | 115887 | Gabriel | Arsenal | missing_in_other | opta_id | 61 |  | 90 |  |
| 4506323 | 115887 | Gabriel Magalhães | Arsenal | missing_in_primary | unresolved |  | 61 |  | 90 |
| 4506377 | 116131 | Kenny Tete | Fulham | null_in_one | name_exact | 0 |  | 8 | 8 |
| 4506570 | 116175 | Hee-Chan Hwang | Wolverhampton Wanderers | missing_in_other | opta_id | 0 |  | 5 |  |
| 4506570 | 116175 | Nico González | Manchester City | null_in_one | name_exact | 0 |  | 1 | 1 |
| 4506570 | 116175 | Hwang Hee-Chan | Wolverhampton Wanderers | missing_in_primary | unresolved |  |  |  | 5 |
| 4813590 | 125006 | Mason Mount | Manchester United | null_in_one | opta_id | 0 |  | 1 | 1 |
| 4813590 | 125006 | Ayden Heaven | Manchester United | null_in_one | opta_id | 0 |  | 1 | 1 |
| 5795443 | 128951 | Daniel Jebbison | AFC Bournemouth | null_in_one | opta_id | 0 |  | 1 | 1 |
| 5795369 | 128929 | Tyrone Mings | Aston Villa | null_in_one | opta_id | 0 |  | 16 | 16 |
| 5795369 | 128929 | Matteo Ruggeri | Aston Villa | null_in_one | opta_id | 0 |  | 8 | 8 |
| 5795369 | 128929 | Alejandro Garnacho | Aston Villa | null_in_one | opta_id | 0 |  | 4 | 4 |
| 5795369 | 128929 | Alysson Edward | Aston Villa | null_in_one | opta_id | 0 |  | 8 | 8 |

## 6. Fetch log summary

| source | status | requests |
|---|---|---|
| fotmob | 200 | 810 |
| fotmob | network_error | 1 |
| premierleague | 200 | 261 |
| premierleague | network_error | 1 |

## 7. Five random player-match rows for manual spot-check

Open `https://www.fotmob.com/match/<match_id>` and compare the player's *Accurate passes* (x/**y**, y = attempted) and minutes.

**Lucas Bergvall** — Tottenham Hotspur v Leicester City (2025-01-26 14:00:00)

```
match_id           4506611
source             fotmob
player_id          1386775
player_name        Lucas Bergvall
team               Tottenham Hotspur
opponent           Leicester City
is_home            True
position           MID
started            True
minutes_played     90
passes_attempted   42
passes_completed   38
subbed_on_minute   None
subbed_off_minute  None
red_card           False
opta_player_id     570526
null_reasons       subbed_off_minute:not_subbed_off;subbed_on_minute:not_subbed_on
fetched_at         2026-09-22 21:16:22
match_date_utc     2025-01-26 14:00:00
home_team          Tottenham Hotspur
away_team          Leicester City
```

**Martin Ødegaard** — Arsenal v Manchester United (2024-12-04 20:15:00)

```
match_id           4506424
source             fotmob
player_id          534670
player_name        Martin Ødegaard
team               Arsenal
opponent           Manchester United
is_home            True
position           MID
started            True
minutes_played     89
passes_attempted   45
passes_completed   40
subbed_on_minute   None
subbed_off_minute  90
red_card           False
opta_player_id     184029
null_reasons       subbed_on_minute:not_subbed_on
fetched_at         2026-09-22 21:11:52
match_date_utc     2024-12-04 20:15:00
home_team          Arsenal
away_team          Manchester United
```

**Fábio Carvalho** — Fulham v Brentford (2025-09-20 19:00:00)

```
match_id           4813419
source             fotmob
player_id          963965
player_name        Fábio Carvalho
team               Brentford
opponent           Fulham
is_home            False
position           FWD
started            False
minutes_played     3
passes_attempted   4
passes_completed   3
subbed_on_minute   87
subbed_off_minute  None
red_card           False
opta_player_id     244858
null_reasons       subbed_off_minute:not_subbed_off
fetched_at         2026-09-22 21:26:18
match_date_utc     2025-09-20 19:00:00
home_team          Fulham
away_team          Brentford
```

**Marc Cucurella** — Chelsea v Manchester United (2026-04-18 19:00:00)

```
match_id           4813697
source             fotmob
player_id          873289
player_name        Marc Cucurella
team               Chelsea
opponent           Manchester United
is_home            True
position           DEF
started            True
minutes_played     90
passes_attempted   45
passes_completed   42
subbed_on_minute   None
subbed_off_minute  None
red_card           False
opta_player_id     179268
null_reasons       subbed_off_minute:not_subbed_off;subbed_on_minute:not_subbed_on
fetched_at         2026-09-22 21:40:09
match_date_utc     2026-04-18 19:00:00
home_team          Chelsea
away_team          Manchester United
```

**Wilfred Ndidi** — Arsenal v Leicester City (2024-09-28 14:00:00)

```
match_id           4506314
source             fotmob
player_id          533228
player_name        Wilfred Ndidi
team               Leicester City
opponent           Arsenal
is_home            False
position           MID
started            True
minutes_played     89
passes_attempted   26
passes_completed   23
subbed_on_minute   None
subbed_off_minute  90
red_card           False
opta_player_id     203341
null_reasons       subbed_on_minute:not_subbed_on
fetched_at         2026-09-22 21:07:37
match_date_utc     2024-09-28 14:00:00
home_team          Arsenal
away_team          Leicester City
```
