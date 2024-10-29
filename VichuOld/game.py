import pygame
import random

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Game settings
GRAVITY = 0.5
FLAP_STRENGTH = -10
PIPE_WIDTH = 70
PIPE_HEIGHT = 400
PIPE_GAP = 150
BIRD_WIDTH = 50
BIRD_HEIGHT = 35

# Load images
BIRD_IMAGE = pygame.image.load('bird.png')
PIPE_IMAGE = pygame.image.load('pipe.png')
BACKGROUND_IMAGE = pygame.image.load('background.png')

# Screen setup
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Flappy Bird')

# Clock
clock = pygame.time.Clock()

class Bird:
    def __init__(self):
        self.image = pygame.transform.scale(BIRD_IMAGE, (BIRD_WIDTH, BIRD_HEIGHT))
        self.x = SCREEN_WIDTH // 4
        self.y = SCREEN_HEIGHT // 2
        self.velocity = 0

    def flap(self):
        self.velocity = FLAP_STRENGTH

    def move(self):
        self.velocity += GRAVITY
        self.y += self.velocity

    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))

class Pipe:
    def __init__(self, x):
        self.x = x
        self.height = random.randint(100, SCREEN_HEIGHT - PIPE_GAP - 100)
        self.top_pipe = pygame.transform.scale(PIPE_IMAGE, (PIPE_WIDTH, self.height))
        self.bottom_pipe = pygame.transform.scale(PIPE_IMAGE, (PIPE_WIDTH, SCREEN_HEIGHT - self.height - PIPE_GAP))

    def move(self):
        self.x -= 5

    def draw(self, screen):
        screen.blit(self.top_pipe, (self.x, -self.height))
        screen.blit(self.bottom_pipe, (self.x, self.height + PIPE_GAP))

def main():
    bird = Bird()
    pipes = [Pipe(SCREEN_WIDTH + i * 200) for i in range(3)]
    score = 0

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    bird.flap()

        bird.move()
        
        for pipe in pipes:
            pipe.move()
            if pipe.x + PIPE_WIDTH < 0:
                pipes.remove(pipe)
                pipes.append(Pipe(SCREEN_WIDTH + 200))
                score += 1
        
        screen.blit(BACKGROUND_IMAGE, (0, 0))
        bird.draw(screen)
        for pipe in pipes:
            pipe.draw(screen)
        
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

if __name__ == "__main__":
    main()
