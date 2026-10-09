#! /bin/bash

if [[ $1 == "test" ]]
then
  PSQL="psql --username=postgres --dbname=worldcuptest -t --no-align -c"
else
  PSQL="psql --username=freecodecamp --dbname=worldcup -t --no-align -c"
fi

# Do not change code above this line. Use the PSQL variable above to query your database.

set -e

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CSV_FILE="$SCRIPT_DIR/games.csv"

$PSQL "TRUNCATE TABLE games, teams;"

team_values=""
game_values=""

while IFS=',' read -r year round winner opponent winner_goals opponent_goals
do
  if [[ "$year" == "year" ]]; then
    continue
  fi

  team_values+="('"$winner"'), ('"$opponent"'), "
  game_values+="($year, '"$round"', (SELECT team_id FROM teams WHERE name = '"$winner"'), (SELECT team_id FROM teams WHERE name = '"$opponent"'), "$winner_goals", "$opponent_goals"), "
done < "$CSV_FILE"

team_values="${team_values%, }"
game_values="${game_values%, }"

$PSQL "INSERT INTO teams (name) VALUES ${team_values} ON CONFLICT (name) DO NOTHING;"
$PSQL "INSERT INTO games (year, round, winner_id, opponent_id, winner_goals, opponent_goals) VALUES ${game_values};"
