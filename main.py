import pygame
from pygame.locals import *
import math
import numpy as np
import random
import sys


class App:
    def __init__(self, screen_size=(600, 600), bg_color=(26, 26, 27)):
        # General setup
        pygame.init()
        self.events = pygame.event.get()
        self.bg_color = bg_color

        # Time
        self.clock = pygame.time.Clock()
        self.current_time, self.start_time = 0, pygame.time.get_ticks()

        # Screen
        self.screen = pygame.display.set_mode(screen_size)
        pygame.display.set_caption('AI Test')

        # Blocks
        self.blocks = Blocks()
        self.filled_blocks = pygame.sprite.Group()

        # Map
        self.map_size = 20
        self.map_generate()

        # AIs
        self.gen = 0
        self.ais = pygame.sprite.Group()
        self.n_ais = 20
        self.ais_generate()
        self.best_score = 0

        # Grid
        self.grid_mode = False
        self.grid_paint_mode = False
        self.grid_erase_mode = False

        # Font
        self.font = pygame.font.SysFont('Consolas', 22)

        self.loop = True

    def run(self):
        while self.loop:
            # Events menagment
            self.event_check()
            # Display draws
            pygame.display.flip()
            self.screen.fill(self.bg_color)
            self.blocks.update()
            self.blocks.draw(self.screen)
            self.ais.update()
            self.ais.draw(self.screen)
            self.show_gen()
            # Time managment
            self.current_time = pygame.time.get_ticks()
            self.gen_timer()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()

    def event_check(self):
        self.events = pygame.event.get()

        for event in self.events:
            # Mouse
            if event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.grid_mode:
                        self.grid_paint_mode = True
                elif event.button == 3:
                    if self.grid_mode:
                        self.grid_erase_mode = True
            elif event.type == MOUSEBUTTONUP:
                if event.button == 1:
                    self.grid_paint_mode = False
                elif event.button == 3:
                    if self.grid_mode:
                        self.grid_erase_mode = False

            # Keys
            if event.type == KEYDOWN:
                if event.key == K_g:
                    if self.grid_mode:
                        self.grid_mode = False
                    else:
                        self.grid_mode = True
                elif event.key == K_F1:
                    self.map_save()
                elif event.key == K_F2:
                    self.map_load()
                elif event.key == K_F3:
                    self.map_reset()

            # Others
            elif event.type == QUIT:
                self.loop = False

    def map_save(self):
        map_list = []
        for blocks_line in self.blocks:
            line = []
            for block in blocks_line:
                if block.filled:
                    line.append(1)
                else:
                    line.append(0)
            map_list.append(line)
        np.save('map', np.array(map_list))
        print('Map saved!')

    def map_load(self):
        map_list = np.ndarray.tolist(np.load('map.npy'))
        j = 0
        for line in self.blocks:
            i = 0
            for block in line:
                if map_list[j][i]:
                    self.filled_blocks.add(block)
                block.filled = map_list[j][i]
                i += 1
            j += 1
        print('Map loaded!')

    def map_reset(self):
        self.filled_blocks.empty()
        for line in self.blocks:
            for block in line:
                block.filled = 0
        print('Map reseted!')

    def map_generate(self, load=True):
        # Grid setup
        last_bottom = 0
        for j in range(self.map_size):
            blocks_line, last_right = pygame.sprite.Group(), 0
            for i in range(self.map_size):
                block = Block(self, 1 / (self.map_size / 10), i, j)
                block.rect.topleft = last_right, last_bottom
                blocks_line.add(block)
                last_right = block.rect.right
            self.blocks.append(blocks_line)
            last_bottom = block.rect.bottom
        # Load map
        if load:
            self.map_load()

    def map_pos(self, index_pos):
        block_size = self.screen.get_width() / self.map_size
        return index_pos[0] * block_size, index_pos[1] * block_size

    def ais_generate(self, winner_list=()):
        self.ais.empty()
        if self.gen == 0:
            for _ in range(self.n_ais):
                ai = AI(self, scale=1 / (self.map_size / 10))
                ai.rect.topleft = self.map_pos((2, 9))
                self.ais.add(ai)
        else:
            '''var_rate = []
            var_rate += round(.5 * self.n_ais) * [.05]
            var_rate += round(.4 * self.n_ais) * [.1]
            var_rate += round(.1 * self.n_ais) * [.5]
            for i in var_rate:
                ai = AI(self, scale=1 / (self.map_size / 10))
                ai.rect.topleft = self.map_pos((2, 9))
                ai.cmd_list = self.randomizer(list(winner_list), percentage=i)
                self.ais.add(ai)'''
            for _ in range(self.n_ais - 1):
                ai = AI(self, scale=1 / (self.map_size / 10), color=Color('white'))
                ai.rect.topleft = self.map_pos((2, 9))
                ai.cmd_list = self.randomizer(list(winner_list))
                self.ais.add(ai)
            ai = AI(self, scale=1 / (self.map_size / 10), color=Color('red'))
            ai.rect.topleft = self.map_pos((2, 9))
            ai.cmd_list = list(winner_list)
            self.ais.add(ai)

    def gen_timer(self, gen_dur=1e4):
        if self.current_time - self.start_time >= gen_dur:
            self.gen += 1
            winner_list = self.get_the_winner()
            self.ais_generate(winner_list)
            self.start_time = pygame.time.get_ticks()

    def get_the_winner(self):
        """Gets the winner and returns it's cmd list"""
        best_score, winner = 0, AI(app)
        for ai in self.ais:
            ai_score = ai.calculate_score()
            if ai_score > best_score:
                best_score = ai_score
                winner = ai
        # print(best_score, len(winner.cmd_list))
        print(f'Best Score: {best_score} | Cmds: {len(winner.cmd_list)}')
        return list(winner.cmd_list)

    @staticmethod
    def randomizer(cmd_list, percentage=.1):
        n_changes = math.floor(len(cmd_list) * percentage)
        for i in range(n_changes):
            cmd_list[random.randrange(0, len(cmd_list))] = 0
        return cmd_list

    def show_gen(self):
        text = self.font.render(f'Generation: {self.gen}', True, Color('white'))
        self.screen.blit(text, (5, 5))


class Block(pygame.sprite.Sprite):
    def __init__(self, application, scale=1., i=0, j=0):
        super().__init__()
        # General setup
        size = application.screen.get_width() * .1 * scale
        self.width, self.height = size, size
        self.color = (120, 120, 120)
        self.filled = 0
        self.pos = i, j

        self.image = pygame.Surface(2 * [size])
        self.image.fill(self.color)
        self.rect = self.image.get_rect()

    def __repr__(self):
        return 'Block at {}'.format(self.pos)

    def update(self):
        if app.grid_mode:
            if self.filled:
                self.image.fill(self.color)
            else:
                self.image.fill(app.bg_color)
                pygame.draw.rect(self.image, self.color, (0, 0, self.width, self.height), width=1)
            if self.rect.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(self.image, (255, 255, 0), (0, 0, self.width, self.height), width=1)
                if app.grid_paint_mode:
                    self.filled = 1
                    app.filled_blocks.add(self)
                elif app.grid_erase_mode:
                    self.filled = 0
                    app.filled_blocks.remove(self)
        else:
            if self.filled:
                self.image.fill(self.color)
            else:
                self.image.fill(app.bg_color)


class Blocks(list):
    def update(self):
        for i in self:
            i.update()

    def draw(self, surface):
        for i in self:
            i.draw(surface)


class AI(pygame.sprite.Sprite):
    def __init__(self, application, scale=1., color=Color('white'), controllable=False):
        super().__init__()
        # General setup
        size = application.screen.get_width() * .1 * scale
        self.controllable = controllable
        self.start_time = pygame.time.get_ticks()

        # Command list
        self.cmd_list = []
        self.cmd_index = 0
        self.cal = 10

        self.image = pygame.Surface(2 * [size], SRCALPHA)
        pygame.draw.ellipse(self.image, color, (0, 0, self.image.get_width(), self.image.get_height()))
        self.rect = self.image.get_rect()

        # Position
        self.pos = self.rect.center

        # Objective
        self.objective = lambda: self.reach_pos_x(application.screen.get_width() + 30)

        self.take_decision()

    def update(self):
        '''if self.controllable:
            self.controller()'''
        if not self.objective():
            try:
                if self.cal == 0:
                    self.cmd_index += 1
                    self.pos = self.rect.center
                    self.cal = 10
                else:
                    if not pygame.sprite.spritecollide(self, app.filled_blocks, False):
                        try:
                            self.cmd_list[self.cmd_index](self)
                            self.cal -= 1
                        except TypeError:
                            self.cmd_list[self.cmd_index] = self.make_decision()
                    else:
                        self.rect.center = self.pos
                        self.cal = 0
            except IndexError:
                self.take_decision()

    def controller(self):
        for event in app.events:
            # Keys
            if event.type == KEYDOWN:
                if event.key == K_d:
                    self.cmd_list.append(self.move_right)
                elif event.key == K_a:
                    self.cmd_list.append(self.move_left)
                elif event.key == K_w:
                    self.cmd_list.append(self.move_up)
                elif event.key == K_s:
                    self.cmd_list.append(self.move_down)

    def move_right(self):
        self.rect.centerx += .1 * app.screen.get_width() / app.map_size

    def move_left(self):
        self.rect.centerx -= .1 * app.screen.get_width() / app.map_size

    def move_up(self):
        self.rect.centery -= .1 * app.screen.get_width() / app.map_size

    def move_down(self):
        self.rect.centery += .1 * app.screen.get_width() / app.map_size

    def take_decision(self):
        self.cmd_list.append(random.choice([AI.move_right,
                                            AI.move_left,
                                            AI.move_up,
                                            AI.move_down]))

    def reach_pos_x(self, pos):
        if self.rect.right > pos:
            return True
        return False

    @staticmethod
    def make_decision():
        return random.choice([AI.move_right,
                              AI.move_left,
                              AI.move_up,
                              AI.move_down])

    def calculate_score(self):
        score = 0
        # Objective
        if self.objective():
            score += 1000
        # Distance from objective
        score += self.rect.left / app.screen.get_width() * 1000
        # Time
        score += self.start_time / app.current_time * 100
        # List len
        score -= len(self.cmd_list)
        return score


if __name__ == '__main__':
    app = App()
    app.run()
