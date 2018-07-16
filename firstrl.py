import libtcodpy as libtcod

# window size
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50

# size of the map
MAP_WIDTH = 80
MAP_HEIGHT = 45

LIMIT_FPS = 20

color_dark_wall = libtcod.Color(0, 0, 100) # dark blue
color_dark_ground = libtcod.Color(50, 50, 150) # dark indigo

#########################
### CLASS DEFINITIONS ###
#########################

class Object:
    # a generic object: player, monster, item, stairs, etc
    # always represented by a character on Screen
    def __init__(self, x, y, char, color):
        self.x = x
        self.y = y
        self.char = char
        self.color = color

    def move(self, dx, dy):
        if not map[self.x + dx][self.y + dy].blocked:
            # move by the given amount
            self.x += dx
            self.y += dy

    def draw(self):
        # set the color and then draw the character that represents this object at its position
        libtcod.console_set_default_foreground(con, self.color)
        libtcod.console_put_char(con, self.x, self.y, self.char, libtcod.BKGND_NONE)

    def clear(self):
        # erase the character that represents the Object
        libtcod.console_put_char(con, self.x, self.y, ' ', libtcod.BKGND_NONE)

class Rect:
    # rectangle on the map, represents a room
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h

class Tile:
    # a map tile and its properties
    def __init__(self, blocked, block_sight = None):
        self.blocked = blocked

        # by default, if a tile is blocked, it will also block sight
        if block_sight is None: block_sight = blocked
        self.block_sight = block_sight

#################
### FUNCTIONS ###
#################

def create_h_tunnel(x1, x2, y):
    # create a horizontal tunnel
    global map
    for x in range(min(x1, x2), max(x1, x2) + 1):
        map[x][y].blocked = False
        map[x][y].block_sight = False

def create_v_tunnel(y1, y2, x):
    # create a vertical tunnel
    global map
    for y in range(min(y1, y2), max(y1, y2) + 1):
        map[x][y].blocked = False
        map[x][y].block_sight = False

def create_room(room):
    global map
    # go through the tiles in the rectangle and make them passable
    for x in range(room.x1 + 1, room.x2):
        for y in range(room.y1 + 1, room.y2):
            map[x][y].blocked = False
            map[x][y].block_sight = False


def handle_keys():

    # misc keys
    key = libtcod.console_wait_for_keypress(True)
    if key.vk == libtcod.KEY_ENTER and key.lalt:
        # Alt+Enter: toggle fullscreen
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
    elif key.vk == libtcod.KEY_ESCAPE:
        return True # exit game

    # movement keys
    if libtcod.console_is_key_pressed(libtcod.KEY_UP):
        player.move(0, -1)
    elif libtcod.console_is_key_pressed(libtcod.KEY_DOWN):
        player.move(0, 1)
    elif libtcod.console_is_key_pressed(libtcod.KEY_LEFT):
        player.move(-1, 0)
    elif libtcod.console_is_key_pressed(libtcod.KEY_RIGHT):
        player.move(1, 0)

def make_map():
    global map

    # fill map with blocked tiles
    map = [[ Tile(True)
        for y in range(MAP_HEIGHT) ]
            for x in range(MAP_WIDTH) ]

    # create two test rooms
    room1 = Rect(20, 15, 10, 15)
    room2 = Rect(50, 15, 10, 15)
    create_room(room1)
    create_room(room2)
    create_h_tunnel(25, 55, 23)
    
def render_all():
    # draw all objects in list
    for object in objects:
        object.draw()

    # go through all tiles and draw them to screen with appropriate background color
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            wall = map[x][y].block_sight
            if wall:
                libtcod.console_set_char_background(con, x, y, color_dark_wall, libtcod.BKGND_SET)
            else:
                libtcod.console_set_char_background(con, x, y, color_dark_ground, libtcod.BKGND_SET)
    
    # blit the contents of the new offscreen console to the root console
    libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)

##################
### GAME LOGIC ###
##################

# Initialization
libtcod.console_set_custom_font('arial10x10.png', libtcod.FONT_TYPE_GRAYSCALE | libtcod.FONT_LAYOUT_TCOD)
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'python/libtcod tutorial', False) # Screen size, title, fullscreen
con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)
libtcod.sys_set_fps(LIMIT_FPS) # Limits FPS if the game is in real time

# Create player
player = Object(SCREEN_WIDTH/2, SCREEN_HEIGHT/2, '@', libtcod.white)
player.x = 25
player.y = 23

# Create NPC
npc = Object(SCREEN_WIDTH/2 - 5, SCREEN_HEIGHT/2, '@', libtcod.yellow)

# list that holds all objects in the game
objects = [npc, player] 

# Construct the map
make_map()

# Main Loop
while not libtcod.console_is_window_closed():
    # render all objects
    render_all()
    
    # present changes to the screen
    libtcod.console_flush()

    # erase objects from previous locations
    for object in objects:
        object.clear()

    # handle keys and exit game if needed
    exit = handle_keys()
    if exit:
        break
