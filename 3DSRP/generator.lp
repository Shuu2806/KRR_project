% 3D Symbolic Region Puzzle Generator

#const c = 12.
#const n = 4.
#const m = 3.
#const k = 2.
#const w = 4.

regions(m).
symbol_type(1..k).
dim(1..n).

% Step 1 : Generate the board
% Select exactly c cubes within the n×n×n bounding box
c { cube(X,Y,Z) : dim(X), dim(Y), dim(Z) } c.

% Board adjacency
adj_board(X,Y,Z, X',Y',Z') :- cube(X,Y,Z), cube(X',Y',Z'),
                               |X-X'| + |Y-Y'| + |Z-Z'| == 1.

% Board connectivity (all cubes reachable from the lex-smallest one)
root_board(X,Y,Z) :- cube(X,Y,Z),
                     not cube(X',Y',Z') : cube(X',Y',Z'), (X',Y',Z') < (X,Y,Z).
reach_board(X,Y,Z) :- root_board(X,Y,Z).
reach_board(X',Y',Z') :- reach_board(X,Y,Z), adj_board(X,Y,Z, X',Y',Z').
:- cube(X,Y,Z), not reach_board(X,Y,Z).

% Board non-planarity: at least 2 distinct values in each axis
:- #count { X : cube(X,Y,Z) } < 2.
:- #count { Y : cube(X,Y,Z) } < 2.
:- #count { Z : cube(X,Y,Z) } < 2.


% Step 2 : Assign regions
% Each cube belongs to exactly one region 1..m
1 { region(X,Y,Z, R) : R = 1..m } 1 :- cube(X,Y,Z).

% Connectivity within each region (no walls yet, use board adjacency)
adj_region(X,Y,Z, X',Y',Z') :- adj_board(X,Y,Z, X',Y',Z'),
                                region(X,Y,Z, R), region(X',Y',Z', R).

root_region(X,Y,Z, R) :- region(X,Y,Z, R),
                          not region(X',Y',Z', R) : cube(X',Y',Z'), (X',Y',Z') < (X,Y,Z).

reach_region(X,Y,Z, R) :- root_region(X,Y,Z, R).
reach_region(X',Y',Z', R) :- reach_region(X,Y,Z, R), adj_region(X,Y,Z, X',Y',Z').

:- region(X,Y,Z, R), not reach_region(X,Y,Z, R).

% Each region must be non-planar (at least 2 distinct values per axis)
:- regions(M), R = 1..M, #count { X : region(X,Y,Z, R) } < 2.
:- regions(M), R = 1..M, #count { Y : region(X,Y,Z, R) } < 2.
:- regions(M), R = 1..M, #count { Z : region(X,Y,Z, R) } < 2.


% Step 3 : Place symbols
% Each region has exactly one cube per symbol type
1 { symbol(X,Y,Z, S) : cube(X,Y,Z), region(X,Y,Z, R) } 1 :- R = 1..m, symbol_type(S).

% No cube carries two different symbols
:- symbol(X,Y,Z, S1), symbol(X,Y,Z, S2), S1 < S2.


% Step 4 : Place walls
% Walls only on boundaries between different regions (canonical: lex-smaller tuple first)
candidate_wall(X,Y,Z, X',Y',Z') :- adj_board(X,Y,Z, X',Y',Z'),
                                    region(X,Y,Z, R1), region(X',Y',Z', R2), R1 != R2,
                                    (X,Y,Z) < (X',Y',Z').

% Select exactly w walls from the boundary
w { wall(X,Y,Z, X',Y',Z') : candidate_wall(X,Y,Z, X',Y',Z') } w.


% Variant Filomino : cell_size_hint
% Active if filomino = 1 (default is 0)
% h cellules aléatoires du plateau sont annotées avec la taille de leur région
% (plusieurs cellules peuvent appartenir à la même région)

#const filomino = 0.
#const h = 3.

region_size(R, S) :- regions(M), R = 1..M,
                     S = #count { X,Y,Z : region(X,Y,Z, R) }.

h { hint_cell(X,Y,Z) : cube(X,Y,Z) } h :- filomino = 1.

cell_size_hint(X,Y,Z, S) :- hint_cell(X,Y,Z), region(X,Y,Z, R), region_size(R, S).


#show cube/3.
#show symbol/4.
#show wall/6.
#show regions/1.
#show symbol_type/1.
#show cell_size_hint/4.