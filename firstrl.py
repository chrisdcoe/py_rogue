import libtcodpy as libtcod

# window size
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50

# size of the map
MAP_WIDTH = 80
MAP_HEIGHT = 45

# room dimensions and quantity
ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30

# field of view
FOV_ALGO = 0 # default FOV algorithm
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 10

# object settings
MAX_ROOM_MONSTERS = 3

# misc settings
LIMIT_FPS = 20

# color definitions
color_dark_wall = libtcod.Color(0, 0, 100) 
color_light_wall = libtcod.Color(130, 110, 50) 
color_dark_ground = libtcod.Color(20, 20, 60) 
color_light_ground = libtcod.Color(50,40,20)

#########################
### CLASS DEFINITIONS ###
#########################

class Object:
    # a generic object: player, monster, item, stairs, etc
    # always represented by a character on Screen
    def __init__(self, x, y, char, name, color, blocks=False):
        self.x = x
        self.y = y
        self.char = char
        self.name = name
        self.color = color
        self.blocks = blocks

    def move(self, dx, dy):
        if not is_blocked(self.x + dx, self.y + dy):
            # move by the given amount
            self.x += dx
            self.y += dy

    def draw(self):
        # only show object if visible to player
        if libtcod.map_is_in_fov(fov_map, self.x, self.y):
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

    def center(self):
        # check center coordinates of room
        center_x = (self.x1 + self.x2) / 2
        center_y = (self.y1 + self.y2) / 2
        return (center_x, center_y)

    def intersect(self, other):
        # return true if this rectangle intersects with another
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)

class Tile:
    # a map tile and its properties
    def __init__(self, blocked, block_sight = None):
        self.blocked = blocked
        self.explored = False

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
    # go through the tiles in the rectangle and make them passable
    global map
    for x in range(room.x1 + 1, room.x2):
        for y in range(room.y1 + 1, room.y2):
            map[x][y].blocked = False
            map[x][y].block_sight = False

def handle_keys():
    global fov_recompute

    # misc keys
    key = libtcod.console_wait_for_keypress(True)
    if key.vk == libtcod.KEY_ENTER and key.lalt:
        # Alt+Enter: toggle fullscreen
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
    elif key.vk == libtcod.KEY_ESCAPE:
        return 'exit' # exit game

    if game_state == 'playing':
        # movement keys
        if libtcod.console_is_key_pressed(libtcod.KEY_UP):
            player_move_or_attack(0, -1)
        elif libtcod.console_is_key_pressed(libtcod.KEY_DOWN):
            player_move_or_attack(0, 1)
        elif libtcod.console_is_key_pressed(libtcod.KEY_LEFT):
            player_move_or_attack(-1, 0)
        elif libtcod.console_is_key_pressed(libtcod.KEY_RIGHT):
            player_move_or_attack(1, 0)
        else:
            return 'didnt-take-turn'

def is_blocked(x, y):
    # test the map tile
    if map[x][y].blocked:
        return True

    # check for any blocking objects
    for object in objects:
        if object.blocks and object.x == x and object.y == y:
            return True

    return False

def make_map():
    global map, player

    # fill map with blocked tiles
    map = [[ Tile(True)
        for y in range(MAP_HEIGHT) ]
            for x in range(MAP_WIDTH) ]

    # iterate until max number of rooms, assigning random coordinates and size
    rooms = []
    num_rooms = 0

    for r in range(MAX_ROOMS):
        # random width and height
        w = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        h = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        # random position without going out of bounds of the map
        x = libtcod.random_get_int(0, 0, MAP_WIDTH - w - 1)
        y = libtcod.random_get_int(0, 0, MAP_HEIGHT - h - 1)

        new_room = Rect(x, y, w, h)

        # check if other rooms intersect with this one
        failed = False
        for other_room in rooms:
            if new_room.intersect(other_room):
                failed = True
                break
        if not failed:
            # there are no intersections, this room is valid
            # draw room to map tiles
            create_room(new_room)

            # find center coordinates of room
            (new_x, new_y) = new_room.center()

            if num_rooms == 0:
                # the first room, where player starts
                player.x = new_x
                player.y = new_y
            else:
                # for all rooms after the first
                # connect it to previous room with a tunnel
                # center coords of previous room
                (prev_x, prev_y) = rooms[num_rooms-1].center()

                # coin toss: horizontal or vertical first?
                if libtcod.random_get_int(0, 0, 1) == 1:
                    # horizontal, then vertical
                    create_h_tunnel(prev_x, new_x, prev_y)
                    create_v_tunnel(prev_y, new_y, new_x)
                else:
                    # vertical, then horizontal
                    create_v_tunnel(prev_y, new_y, prev_x)
                    create_h_tunnel(prev_x, new_x, new_y)
            
            # add contents to room (monsters etc)
            place_objects(new_room)

            # append new rooms to list
            rooms.append(new_room)
            num_rooms += 1
            
def place_objects(room):
    # choose random number of monsters
    num_monsters = libtcod.random_get_int(0, 0, MAX_ROOM_MONSTERS)

    for i in range(num_monsters):
        # choose random spot for monster
        x = libtcod.random_get_int(0, room.x1, room.x2)
        y = libtcod.random_get_int(0, room.y1, room.y2)

        # only place monster of tile is not blocked
        if not is_blocked(x, y):
            # choose random monster type
            choice = libtcod.random_get_int(0, 0, 100)
            if choice < 10: # 10%
                # create troll
                monster = Object(x, y, 'T', 'troll', libtcod.darker_green, blocks=True)
            elif choice < 10+20: # 20%
                # create gnoll
                monster = Object(x, y, 'G', 'gnoll', libtcod.dark_amber, blocks=True)
            elif choice < 10+20+30: # 30%
                # create orc
                monster = Object(x, y, 'o', 'orc', libtcod.desaturated_green, blocks=True)
            else: # 40%
                # create kobold
                monster = Object(x, y, 'g', 'goblin', libtcod.desaturated_crimson, blocks=True)
            objects.append(monster)

def player_move_or_attack(dx, dy):
    global fov_recompute

    # the coordinates the player is moving to or attacking
    x = player.x + dx
    y = player.y + dy

    # try to find an attackable object there
    target = None
    for object in objects:
        if object.x == x and object.y == y:
            target = object
            break

    # attack if target found, otherwise move
    if target is not None:
        print 'The ' + target.name + ' laughs at your puny attack!'
    else:
        player.move(dx, dy)
        fov_recompute = True

def render_all():
    global fov_map, color_dark_wall, color_light_wall
    global color_dark_ground, color_light_ground
    global fov_recompute
    
    if fov_recompute:
        # recompute FOV if needed (such as player moving)
        fov_recompute = False
        libtcod.map_compute_fov(fov_map, player.x, player.y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALGO)

        # go through all tiles and draw them to screen with appropriate background color
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                visible = libtcod.map_is_in_fov(fov_map, x, y)
                wall = map[x][y].block_sight
                if not visible:
                    # aka it's out of player's FOV
                    # if it's not visible right now, player can only see it if it's explored
                    if map[x][y].explored:
                        if wall:
                            libtcod.console_set_char_background(con, x, y, color_dark_wall, libtcod.BKGND_SET)
                        else:
                            libtcod.console_set_char_background(con, x, y, color_dark_ground, libtcod.BKGND_SET)
                else:
                    # it is visible
                    if wall:
                        libtcod.console_set_char_background(con, x, y, color_light_wall, libtcod.BKGND_SET)
                    else:
                        libtcod.console_set_char_background(con, x, y, color_light_ground, libtcod.BKGND_SET)
                    map[x][y].explored = True

    # draw all objects in list
    for object in objects:
        object.draw()

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
player = Object(0, 0, '@', 'player', libtcod.white, blocks=True)

# list of objects starting with player
objects = [player] 

# Construct the map
make_map()

# Create field of vision map
fov_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
for y in range(MAP_HEIGHT):
    for x in range(MAP_WIDTH):
        libtcod.map_set_properties(fov_map, x, y, not map[x][y].block_sight, not map[x][y].blocked)

fov_recompute = True
game_state = 'playing'
player_action = None

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
    player_action = handle_keys()
    if player_action == 'exit':
        break

    # let monsters take their turn
    if game_state == 'playing' and player_action != 'didnt-take-turn':
        for object in objects:
            if object != player:
                print 'The ' + object.name + ' growls!'
            

