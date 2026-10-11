#!/bin/bash

PSQL="psql --username=freecodecamp --dbname=number_guess -t --no-align -c"

SECRET_NUMBER=$((RANDOM % 1000 + 1))
NUMBER_OF_GUESSES=1

echo "Enter your username:"
read USERNAME

USER_ID=$($PSQL "SELECT user_id FROM users WHERE username='$USERNAME'")
if [[ -z $USER_ID ]]; then
  echo "Welcome, $USERNAME! It looks like this is your first time here."
  $PSQL "INSERT INTO users(username, games_played, best_game) VALUES('$USERNAME', 0, 0)" > /dev/null
else
  GAMES_PLAYED=$($PSQL "SELECT games_played FROM users WHERE user_id=$USER_ID")
  BEST_GAME=$($PSQL "SELECT best_game FROM users WHERE user_id=$USER_ID")
  echo "Welcome back, $USERNAME! You have played $GAMES_PLAYED games, and your best game took $BEST_GAME guesses."
fi

echo "Guess the secret number between 1 and 1000:"
read GUESS

while [[ "$GUESS" != "$SECRET_NUMBER" ]]; do
  if [[ ! $GUESS =~ ^[0-9]+$ ]]; then
    echo "That is not an integer, guess again:"
  elif (( GUESS > SECRET_NUMBER )); then
    echo "It's lower than that, guess again:"
  else
    echo "It's higher than that, guess again:"
  fi
  read GUESS
  NUMBER_OF_GUESSES=$((NUMBER_OF_GUESSES + 1))
done

echo "You guessed it in $NUMBER_OF_GUESSES tries. The secret number was $SECRET_NUMBER. Nice job!"

if [[ -z $USER_ID ]]; then
  USER_ID=$($PSQL "SELECT user_id FROM users WHERE username='$USERNAME'")
fi
$PSQL "UPDATE users SET games_played = games_played + 1, best_game = CASE WHEN games_played = 0 OR best_game = 0 OR $NUMBER_OF_GUESSES < best_game THEN $NUMBER_OF_GUESSES ELSE best_game END WHERE user_id=$USER_ID" > /dev/null
