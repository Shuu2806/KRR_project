% 3D Symbolic Region Puzzle Solver

% input fact provided by an instance of a puzzle : 
% cube(X,Y,Z)               : a cell of the board
% symbol(X,Y,Z,S)           : a Symbol S at cell (X,Y,Z)
% wall(x,y,z,x',y',z')      : a wall between to adjacent cubes
% regions(M)                : required number of regions
% symbol_type(S)            : symbol types
% cell_size_hint(X,Y,Z,S) : (optional) the size S of the region of the cube


% Ensure the wall are symmetric
s_wall(X,Y,Z, X',Y',Z') :- wall(X,Y,Z, X',Y',Z').
s_wall(X',Y',Z', X,Y,Z) :- wall(X,Y,Z, X',Y',Z').


% Rule 1 : Coverage

% Every Cube is assigned to exactly one region
1 { region(X,Y,Z, R) : R = 1..M } 1 :- cube(X,Y,Z), regions(M).


% Rule 2 : Connectivity

% Cubes are face-adjacent if they differ by 1 in exactly one coordinate
adj_board(X,Y,Z, X',Y',Z') :- cube(X,Y,Z), cube(X',Y',Z'),|X-X'| + |Y-Y'| + |Z-Z'| == 1.

% Two adjacent cubes are connected if there is no wall between them
adj(X,Y,Z, X',Y',Z') :- adj_board(X,Y,Z, X',Y',Z'),not s_wall(X,Y,Z, X',Y',Z').

% Adjacency within the same region
adj_region(X,Y,Z, X',Y',Z') :- adj(X,Y,Z, X',Y',Z'),region(X,Y,Z, R), region(X',Y',Z', R).

% Root of each region: lexicographically smallest cube in the region
root(X,Y,Z, R) :- region(X,Y,Z, R),not region(X',Y',Z', R) : cube(X',Y',Z'), (X',Y',Z') < (X,Y,Z).

% Reachability from the root within the region
reachable(X,Y,Z, R) :- root(X,Y,Z, R).
reachable(X',Y',Z', R) :- reachable(X,Y,Z, R), adj_region(X,Y,Z, X',Y',Z').

% Constraint: all cubes in a region must be reachable from its root
:- region(X,Y,Z, R), not reachable(X,Y,Z, R).


% Rule 3 : Non-planar

% Each region must extend in all three spatial dimensions
distinct_x(R, X) :- region(X,Y,Z, R).
distinct_y(R, Y) :- region(X,Y,Z, R).
distinct_z(R, Z) :- region(X,Y,Z, R).

:- regions(M), R = 1..M, #count { X : distinct_x(R, X) } < 2.
:- regions(M), R = 1..M, #count { Y : distinct_y(R, Y) } < 2.
:- regions(M), R = 1..M, #count { Z : distinct_z(R, Z) } < 2.


% Rule 4 : Symbol 

% Each region contains exactly one cube with each symbol type
:- regions(M), R = 1..M, symbol_type(S), #count { X,Y,Z : region(X,Y,Z, R), symbol(X,Y,Z, S) } != 1.


% Rule 5 : Wall
% Cubes separated by a wall must belong to different regions
:- s_wall(X,Y,Z, X',Y',Z'), region(X,Y,Z, R), region(X',Y',Z', R).


% Rule Variant Fillomino
% The size of the cube region is equal to S

% Upper bound — fires during construction as soon as a region exceeds S cubes.
% Clingo propagates this the moment the (S+1)-th cube is tentatively added to R,
% pruning the branch immediately without finishing the assignment.
:- cell_size_hint(X, Y, Z, S), region(X, Y, Z, R),
   S+1 { region(X',Y',Z', R) : cube(X',Y',Z') }.

% Lower bound — the region must have at least S cubes.
:- cell_size_hint(X, Y, Z, S), region(X, Y, Z, R),
   #count { X',Y',Z' : region(X',Y',Z', R) } < S.

% Mutual exclusion — two hints with different sizes cannot share a region.
% Binary constraint: fires as soon as both cubes are assigned to the same R,
% long before the count is complete.
:- cell_size_hint(X1, Y1, Z1, S1), cell_size_hint(X2, Y2, Z2, S2), S1 != S2,
   region(X1, Y1, Z1, R), region(X2, Y2, Z2, R).

#show region/4.