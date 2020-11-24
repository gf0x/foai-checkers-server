import asyncio
import logging
import secrets

from main import game


class GameError(Exception):
    pass


class ForbiddenMoveError(GameError):
    pass


class MoveIsNotPossible(GameError):
    pass


class Game:
    def __init__(self):
        self._game = game
        self._is_started = False
        self._is_finished = False
        self._available_move_time = 3.2  # 200 ms plus, cause for network latency
        self._available_current_move_time = self._available_move_time
        self._players = {}
        self._lost_time_player = None
        self._colors_table = {
            1: 'BLACK',
            2: 'RED'
        }

    def _whose_turn(self):
        return self._colors_table[self._game.whose_turn()]

    def _status(self):
        if not self._is_started:
            return 'Not yet started'
        if self._lost_time_player:
            return f'Player {self._colors_table[self._lost_time_player]} reached time limit'
        return 'Game is over' if self._game.is_over() else 'Game is playing'

    def _winner(self):
        if self._lost_time_player:
            return self._colors_table[1] \
                if self._lost_time_player == 2 \
                else self._colors_table[2]
        return self._colors_table[self._game.get_winner()] if self._game.get_winner() else None

    def _board(self):
        output = []

        for piece in self._game.board.pieces:
            if not piece.captured:
                output.append({
                    'color': 'RED' if piece.player == 2 else 'BLACK',
                    'row': piece.get_row(),
                    'column': piece.get_column(),
                    'king': piece.king,
                    'position': piece.position
                })

        return output

    def add_player(self, team_name):
        if self._is_started:
            return

        player_num = 2 if 1 in self._players else 1

        token = secrets.token_hex(16)
        self._players[player_num] = {
            'token': token,
            'team_name': team_name
        }

        if 1 in self._players and 2 in self._players:
            asyncio.ensure_future(self.start())

        return {
            'color': self._colors_table[player_num],
            'token': token
        }

    async def start(self):
        logging.info('...GAME IS STARTED...')
        logging.info(
            f'1 player, color: {self._colors_table[1]}, team name: {self._players[1]["team_name"]}'
        )
        logging.info(
            f'2 player, color: {self._colors_table[2]}, team name: {self._players[2]["team_name"]}'
        )

        self._is_started = True

        while True:
            await asyncio.sleep(0.05)

            self._available_current_move_time -= 0.05

            if self._available_current_move_time < 0:
                self._lost_time_player = self._game.whose_turn()
                self._is_finished = True
                break

            if self._game.is_over():
                self._is_finished = True
                break

    def move(self, token, move):
        player = self._players[self._game.whose_turn()]
        if player['token'] != token:
            raise ForbiddenMoveError
        try:
            self._game.move(move)
            self._available_current_move_time = self._available_move_time
        except ValueError as e:
            raise MoveIsNotPossible(str(e))

    def is_started(self):
        return self._is_started

    def is_finished(self):
        return self._is_finished

    @property
    def json(self):
        return {
            'status': self._status(),
            'whose_turn': self._whose_turn(),
            'winner': self._winner(),
            'board': self._board(),
            'available_time': self._available_current_move_time,
            'is_started': self.is_started(),
            'is_finished': self.is_finished()
        }
