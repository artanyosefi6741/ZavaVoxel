from ursina import *
from ursina.mesh import Mesh
from math import sin, cos, floor

print("ok")

# ============================================================
# ZAVAVOXEL alpha 0.1
# CLEAN VOXEL CORE
# ============================================================
#
# Included:
#   - Voxel terrain
#   - Texture atlas
#   - Grass
#   - Dirt
#   - Stone
#   - Log
#   - Leaves
#   - Water
#   - Trees
#   - Caves
#   - Chunk meshing
#   - Player movement
#   - Voxel collision
#   - Gravity
#   - Jumping
#   - Skybox
#   - Day/night
#
# Not yet:
#   - Ores
#   - Mobs
#   - Structures
#   - Music
#   - Block breaking
#   - Block placing
#
# Files:
#
#   main.py
#   atlas.png
#   meme_skybox.png
#
# ============================================================


app = Ursina()


# ============================================================
# SETTINGS
# ============================================================

window.title = 'ZavaVoxel alpha 0.1'

window.borderless = False

window.fps_counter.enabled = True

application.target_fps = 120

MUSIC_FILE = 'gigachad.ogg'
MUSIC_VOLUME = 0.35

ATLAS_FILE = 'atlas.png'

SKYBOX_FILE = 'meme_skybox.png'


ATLAS_WIDTH = 4096

ATLAS_HEIGHT = 2048


CHUNK_SIZE = 16

WORLD_HEIGHT = 32

WORLD_RADIUS = 2

WORLD_BORDER = WORLD_RADIUS * CHUNK_SIZE

WATER_LEVEL = 7

SEED = 19427


# ============================================================
# PLAYER
# ============================================================

PLAYER_WIDTH = 0.65

PLAYER_HEIGHT = 1.8

PLAYER_EYE_HEIGHT = 1.62

PLAYER_SPEED = 5.0

PLAYER_GRAVITY = 18.0

PLAYER_JUMP = 8.1


# ============================================================
# BLOCK IDS
# ============================================================

AIR = 0

GRASS = 1

DIRT = 2

STONE = 3

LOG = 4

LEAVES = 5

WATER = 6


SOLID_BLOCKS = {
    GRASS,
    DIRT,
    STONE,
    LOG,
    LEAVES,
}

# ============================================================
# BLOCK INTERACTION
# ============================================================

HOTBAR_BLOCKS = [
    GRASS,
    DIRT,
    STONE,
    LOG,
    LEAVES,
    WATER,
]

selected_block = 0

REACH_DISTANCE = 6

# ============================================================
# TEXTURE ATLAS
# ============================================================
#
# Coordinates come directly from the MaxRects JSON.
#
# Atlas origin:
#     top-left
#
# UV origin:
#     bottom-left
#
# ============================================================

ATLAS_SPRITES = {

    GRASS: {
        'x': 1041,
        'y': 607,
        'w': 298,
        'h': 270,
    },

    DIRT: {
    'x': 722,
    'y': 0,
    'w': 720,
    'h': 605,
},

STONE: {
    'x': 722,
    'y': 607,
    'w': 317,
    'h': 276,
},

    LOG: {
        'x': 0,
        'y': 0,
        'w': 720,
        'h': 742,
    },

    LEAVES: {
        'x': 1444,
        'y': 0,
        'w': 718,
        'h': 684,
    },

    WATER: {
        'x': 0,
        'y': 744,
        'w': 288,
        'h': 281,
    },
}


# ============================================================
# WORLD
# ============================================================

world = {}

terrain_heights = {}

chunk_entities = {}


# ============================================================
# DETERMINISTIC RANDOM
# ============================================================

def random_value(x, y, z, salt=0):

    value = (
        x * 73428767
        + y * 912931
        + z * 19349663
        + salt * 83492791
        + SEED
    )

    value ^= value >> 13

    value *= 1274126177

    value ^= value >> 16

    return (
        abs(value) % 100000
    ) / 100000.0


# ============================================================
# TERRAIN
# ============================================================

def get_terrain_height(x, z):

    height = 10

    height += int(
        sin(x * 0.10) * 3
    )

    height += int(
        cos(z * 0.13) * 3
    )

    height += int(
        sin((x + z) * 0.055) * 4
    )

    height += int(
        cos((x - z) * 0.035) * 2
    )

    return max(
        3,
        min(
            WORLD_HEIGHT - 5,
            height
        )
    )


# ============================================================
# CAVE NOISE
# ============================================================

def cave_noise(x, y, z):

    a = sin(
        x * 0.19
        + y * 0.13
        + z * 0.17
    )

    b = cos(
        x * 0.11
        - y * 0.21
        + z * 0.14
    )

    c = sin(
        (x + z) * 0.09
        + y * 0.16
    )

    return (
        a + b + c
    ) / 3.0


def should_make_cave(x, y, z, surface):

    if y <= 2:
        return False

    if y >= surface - 3:
        return False

    return cave_noise(
        x,
        y,
        z
    ) > 0.64


# ============================================================
# TREE
# ============================================================

def make_tree(x, y, z):

    # Trunk

    for ty in range(
        y,
        y + 4
    ):

        world[
            (x, ty, z)
        ] = LOG


    # Leaves

    for lx in range(
        x - 2,
        x + 3
    ):

        for lz in range(
            z - 2,
            z + 3
        ):

            for ly in range(
                y + 2,
                y + 6
            ):

                distance = (
                    abs(lx - x)
                    + abs(lz - z)
                )


                if distance > 3:

                    continue


                if random_value(
                    lx,
                    ly,
                    lz,
                    47
                ) < 0.15:

                    continue


                position = (
                    lx,
                    ly,
                    lz
                )


                if world.get(
                    position,
                    AIR
                ) == AIR:

                    world[position] = LEAVES


# ============================================================
# WORLD GENERATION
# ============================================================

def generate_world():

    world.clear()

    terrain_heights.clear()


    radius = (
        WORLD_RADIUS
        * CHUNK_SIZE
    )


    # --------------------------------------------------------
    # TERRAIN
    # --------------------------------------------------------

    for x in range(
        -radius,
        radius + 1
    ):

        for z in range(
            -radius,
            radius + 1
        ):

            surface = get_terrain_height(
                x,
                z
            )


            terrain_heights[
                (x, z)
            ] = surface


            for y in range(
                0,
                surface + 1
            ):

                if y == surface:

                    block = GRASS

                elif y >= surface - 3:

                    block = DIRT

                else:

                    block = STONE


                if should_make_cave(
                    x,
                    y,
                    z,
                    surface
                ):

                    block = AIR


                world[
                    (x, y, z)
                ] = block


            # ------------------------------------------------
            # WATER
            # ------------------------------------------------

            if surface < WATER_LEVEL:

                for y in range(
                    surface + 1,
                    WATER_LEVEL + 1
                ):

                    world[
                        (x, y, z)
                    ] = WATER

                 # ========================================================
    # SMALL CAVE ENTRANCES
    # ========================================================

    for x in range(
        -radius,
        radius + 1
    ):

        for z in range(
            -radius,
            radius + 1
        ):

            surface = terrain_heights.get(
                (x, z),
                WATER_LEVEL
            )

            if surface <= WATER_LEVEL:
                continue

            # Deterministic random value.
            cave_seed = (
                x * 73428767
                + z * 19349663
                + SEED
            )

            cave_seed ^= cave_seed >> 13
            cave_seed *= 1274126177
            cave_seed ^= cave_seed >> 16

            cave_random = (
               abs(cave_seed) % 100000
            ) / 100000.0

            # Only a small number of entrances.
            if cave_random > 0.035:
              continue

            # ------------------------------------------------
            # SMALL CAVE TUNNEL
            # ------------------------------------------------

            for depth in range(7):

                y = surface - 1 - depth

                center_x = (
                    x
                    + int(
                        sin(depth * 0.8 + x) * 0.5
                    )
                )

                center_z = (
                    z
                    + int(
                        cos(depth * 0.7 + z) * 0.5
                    )
                )

                for dx in range(-1, 2):

                   for dz in range(-1, 2):

                      for dy in range(-1, 2):

                       # Smaller cave entrance
                         if (
                          abs(dx) + abs(dy) + abs(dz)
                             > 1
                        ):
                            continue
                            cave_position = (
                                center_x + dx,
                                y + dy,
                                center_z + dz
                            )

                            if cave_position[1] <= 2:
                                continue

                            world[cave_position] = AIR

    # --------------------------------------------------------
    # TREES
    #
    # Keep spawn area clear.
    # --------------------------------------------------------

    for x in range(
        -radius,
        radius + 1
    ):

        for z in range(
            -radius,
            radius + 1
        ):

            if abs(x) <= 3 and abs(z) <= 3:

                continue


            surface = terrain_heights[
                (x, z)
            ]


            if world.get(
                (x, surface, z),
                AIR
            ) != GRASS:

                continue


            if surface < WATER_LEVEL:

                continue


            if random_value(
                x,
                surface,
                z,
                73
            ) < 0.975:

                continue


            make_tree(
                x,
                surface + 1,
                z
            )


# ============================================================
# FACE DATA
# ============================================================

FACES = [

    # --------------------------------------------------------
    # TOP
    # --------------------------------------------------------

    (
        (0, 1, 0),

        [
            (0, 1, 0),
            (1, 1, 0),
            (1, 1, 1),
            (0, 1, 1),
        ]
    ),


    # --------------------------------------------------------
    # BOTTOM
    # --------------------------------------------------------

    (
        (0, -1, 0),

        [
            (0, 0, 0),
            (0, 0, 1),
            (1, 0, 1),
            (1, 0, 0),
        ]
    ),


    # --------------------------------------------------------
    # FRONT
    # --------------------------------------------------------

    (
        (0, 0, 1),

        [
            (0, 0, 1),
            (1, 0, 1),
            (1, 1, 1),
            (0, 1, 1),
        ]
    ),


    # --------------------------------------------------------
    # BACK
    # --------------------------------------------------------

    (
        (0, 0, -1),

        [
            (1, 0, 0),
            (0, 0, 0),
            (0, 1, 0),
            (1, 1, 0),
        ]
    ),


    # --------------------------------------------------------
    # RIGHT
    # --------------------------------------------------------

    (
        (1, 0, 0),

        [
            (1, 0, 1),
            (1, 0, 0),
            (1, 1, 0),
            (1, 1, 1),
        ]
    ),


    # --------------------------------------------------------
    # LEFT
    # --------------------------------------------------------

    (
        (-1, 0, 0),

        [
            (0, 0, 0),
            (0, 1, 0),
            (0, 1, 1),
            (0, 0, 1),
        ]
    ),
]


# ============================================================
# ATLAS UV
# ============================================================

def get_block_uvs(block):

    sprite = ATLAS_SPRITES[block]


    x = sprite['x']

    y = sprite['y']

    w = sprite['w']

    h = sprite['h']


    u0 = (
        x
        / ATLAS_WIDTH
    )


    u1 = (
        x + w
    ) / ATLAS_WIDTH


    v_top = (
        1.0
        - (
            y
            / ATLAS_HEIGHT
        )
    )


    v_bottom = (
        1.0
        - (
            (y + h)
            / ATLAS_HEIGHT
        )
    )


    return [

        (u0, v_bottom),

        (u1, v_bottom),

        (u1, v_top),

        (u0, v_top),

    ]


# ============================================================
# ADD FACE
# ============================================================

def add_face(
    vertices,
    triangles,
    uvs,
    x,
    y,
    z,
    face,
    block
):

    corners = face[1]

    start = len(vertices)


    # Vertices

    for vx, vy, vz in corners:

        vertices.append(
            (
                x + vx,
                y + vy,
                z + vz
            )
        )


    # Two triangles

    triangles.append(
        (
            start,
            start + 1,
            start + 2
        )
    )


    triangles.append(
        (
            start,
            start + 2,
            start + 3
        )
    )


    # Texture

    uvs.extend(
        get_block_uvs(block)
    )


# ============================================================
# BUILD TERRAIN CHUNK
# ============================================================

def build_chunk(cx, cz):

    vertices = []

    triangles = []

    uvs = []


    start_x = (
        cx * CHUNK_SIZE
    )

    start_z = (
        cz * CHUNK_SIZE
    )


    end_x = (
        start_x
        + CHUNK_SIZE
    )

    end_z = (
        start_z
        + CHUNK_SIZE
    )


    for x in range(
        start_x,
        end_x
    ):

        for z in range(
            start_z,
            end_z
        ):

            for y in range(
                0,
                WORLD_HEIGHT + 1
            ):

                block = world.get(
                    (x, y, z),
                    AIR
                )


                if block == AIR:

                    continue


                # Water uses separate geometry.

                if block == WATER:

                    continue


                for face in FACES:

                    direction = face[0]

                    dx, dy, dz = direction


                    neighbor = world.get(
                        (
                            x + dx,
                            y + dy,
                            z + dz
                        ),
                        AIR
                    )


                    # Don't render faces inside
                    # other solid blocks.

                    if neighbor in SOLID_BLOCKS:

                    # TEMPORARY TEST:
                     # Don't cull neighboring solid blocks.
                     continue


                    add_face(
                        vertices,
                        triangles,
                        uvs,
                        x,
                        y,
                        z,
                        face,
                        block
                    )


    if not vertices:

        return None


    mesh = Mesh(
        vertices=vertices,
        triangles=triangles,
        uvs=uvs,
        mode='triangle'
    )


    mesh.generate()


    mesh.double_sided = True


    entity = Entity(
        model=mesh,
        texture=ATLAS_FILE
    )


    entity.double_sided = True


    return entity


# ============================================================
# BUILD WATER
# ============================================================

def build_water_chunk(cx, cz):

    vertices = []

    triangles = []

    uvs = []


    start_x = (
        cx * CHUNK_SIZE
    )

    start_z = (
        cz * CHUNK_SIZE
    )


    end_x = (
        start_x
        + CHUNK_SIZE
    )

    end_z = (
        start_z
        + CHUNK_SIZE
    )


    for x in range(
        start_x,
        end_x
    ):

        for z in range(
            start_z,
            end_z
        ):

            surface = terrain_heights.get(
                (x, z),
                WATER_LEVEL
            )


            if surface >= WATER_LEVEL:

                continue


            if world.get(
                (
                    x,
                    WATER_LEVEL,
                    z
                ),
                AIR
            ) != WATER:

                continue


            y = WATER_LEVEL - 0.08


            start = len(vertices)


            vertices.extend([

                (
                    x,
                    y,
                    z
                ),

                (
                    x + 1,
                    y,
                    z
                ),

                (
                    x + 1,
                    y,
                    z + 1
                ),

                (
                    x,
                    y,
                    z + 1
                ),

            ])


            triangles.append(
                (
                    start,
                    start + 1,
                    start + 2
                )
            )


            triangles.append(
                (
                    start,
                    start + 2,
                    start + 3
                )
            )


            uvs.extend(
                get_block_uvs(WATER)
            )


    if not vertices:

        return None


    mesh = Mesh(
        vertices=vertices,
        triangles=triangles,
        uvs=uvs,
        mode='triangle'
    )


    mesh.generate()

    mesh.double_sided = True


    entity = Entity(
        model=mesh,
        texture=ATLAS_FILE
    )


    entity.double_sided = True

    entity.alpha = 0.72


    return entity


# ============================================================
# BUILD ALL CHUNKS
# ============================================================

def build_world():

    chunk_entities.clear()


    for cx in range(
        -WORLD_RADIUS,
        WORLD_RADIUS + 1
    ):

        for cz in range(
            -WORLD_RADIUS,
            WORLD_RADIUS + 1
        ):

            terrain_entity = build_chunk(
                cx,
                cz
            )


            water_entity = build_water_chunk(
                cx,
                cz
            )


            chunk_entities[
                (cx, cz)
            ] = (
                terrain_entity,
                water_entity
            )


# ============================================================
# COLLISION
# ============================================================

def is_solid_block(x, y, z):

    block = world.get(
        (
            int(floor(x)),
            int(floor(y)),
            int(floor(z))
        ),
        AIR
    )


    return block in SOLID_BLOCKS


def player_collides(position):

    px = position.x

    py = position.y

    pz = position.z


    half_width = (
        PLAYER_WIDTH / 2
    )


    min_x = int(
        floor(
            px - half_width
        )
    )


    max_x = int(
        floor(
            px + half_width
            - 0.0001
        )
    )


    min_y = int(
        floor(py)
    )


    max_y = int(
        floor(
            py + PLAYER_HEIGHT
            - 0.0001
        )
    )


    min_z = int(
        floor(
            pz - half_width
        )
    )


    max_z = int(
        floor(
            pz + half_width
            - 0.0001
        )
    )


    for x in range(
        min_x,
        max_x + 1
    ):

        for y in range(
            min_y,
            max_y + 1
        ):

            for z in range(
                min_z,
                max_z + 1
            ):

                if is_solid_block(
                    x,
                    y,
                    z
                ):

                    return True


    return False


# ============================================================
# SAFE MOVE
# ============================================================

def move_axis(
    entity,
    axis,
    amount
):

    if amount == 0:
        return False

    position = Vec3(
        entity.position
    )

    if axis == 'x':
        position.x += amount

    elif axis == 'y':
        position.y += amount

    elif axis == 'z':
        position.z += amount

    # --------------------------------------------------------
    # WORLD BORDER
    # --------------------------------------------------------

    border = WORLD_BORDER - 0.35

    if position.x < -border:
        return False

    if position.x > border:
        return False

    if position.z < -border:
        return False

    if position.z > border:
        return False

    # --------------------------------------------------------
    # BLOCK COLLISION
    # --------------------------------------------------------

    if not player_collides(position):
        entity.position = position
        return True

    return False


# ============================================================
# GIGA PLAYER
# ============================================================

class GigaPlayer(Entity):

    def __init__(self):

        super().__init__()


        self.velocity_y = 0.0

        self.grounded = False


        # Camera

        camera.parent = self

        camera.position = (
            0,
            PLAYER_EYE_HEIGHT,
            0
        )


        camera.rotation = (
            0,
            0,
            0
        )


        camera.fov = 90


        mouse.locked = True


    def update(self):

        # ----------------------------------------------------
        # CAMERA
        # ----------------------------------------------------

        if mouse.locked:

            self.rotation_y += (
                mouse.velocity[0]
                * 40
            )


            camera.rotation_x -= (
                mouse.velocity[1]
                * 40
            )


            camera.rotation_x = clamp(
                camera.rotation_x,
                -89,
                89
            )


        # ----------------------------------------------------
        # MOVEMENT
        # ----------------------------------------------------

        forward = Vec3(
            self.forward.x,
            0,
            self.forward.z
        )


        right = Vec3(
            self.right.x,
            0,
            self.right.z
        )


        if forward.length() > 0:

            forward = forward.normalized()


        if right.length() > 0:

            right = right.normalized()


        movement = Vec3(
            0,
            0,
            0
        )


        if held_keys['w']:

            movement += forward


        if held_keys['s']:

            movement -= forward


        if held_keys['d']:

            movement += right


        if held_keys['a']:

            movement -= right


        if movement.length() > 0:

            movement = (
                movement.normalized()
                * PLAYER_SPEED
                * time.dt
            )


        # ----------------------------------------------------
        # HORIZONTAL COLLISION
        # ----------------------------------------------------

        move_axis(
            self,
            'x',
            movement.x
        )


        move_axis(
            self,
            'z',
            movement.z
        )


        # ----------------------------------------------------
        # GROUND CHECK
        # ----------------------------------------------------

        ground_test = Vec3(
            self.position
        )


        ground_test.y -= 0.06


        self.grounded = player_collides(
            ground_test
        )


        # ----------------------------------------------------
        # GRAVITY
        # ----------------------------------------------------

        self.velocity_y -= (
            PLAYER_GRAVITY
            * time.dt
        )


        vertical_motion = (
            self.velocity_y
            * time.dt
        )


        if vertical_motion != 0:

            moved = move_axis(
                self,
                'y',
                vertical_motion
            )


            if not moved:

                self.velocity_y = 0


                if vertical_motion < 0:

                    self.grounded = True


        # ----------------------------------------------------
        # FALL RESET
        # ----------------------------------------------------

        if self.y < -20:

            surface = terrain_heights.get(
                (0, 0),
                WATER_LEVEL
            )


            self.position = (
                0.5,
                surface + 1.05,
                0.5
            )


            self.velocity_y = 0


    def jump(self):

        test = Vec3(
            self.position
        )


        test.y -= 0.07


        if player_collides(test):

            self.velocity_y = PLAYER_JUMP

# ============================================================
# VOXEL RAYCAST
# ============================================================

def raycast_voxel():

    origin = camera.world_position
    direction = camera.forward.normalized()

    previous = None

    step = 0.05
    distance = 0.0

    while distance <= REACH_DISTANCE:

        position = origin + direction * distance

        voxel = (
            floor(position.x),
            floor(position.y),
            floor(position.z)
        )

        block = world.get(voxel, AIR)

        if block != AIR:
            return voxel, previous

        previous = voxel

        distance += step

    return None, None

# ============================================================
# SKYBOX
# ============================================================

def build_skybox():

    size = 400


    vertices = [

        # FRONT

        (-size, -size, size),
        ( size, -size, size),
        ( size,  size, size),
        (-size,  size, size),


        # BACK

        ( size, -size, -size),
        (-size, -size, -size),
        (-size,  size, -size),
        ( size,  size, -size),


        # RIGHT

        ( size, -size, size),
        ( size, -size, -size),
        ( size,  size, -size),
        ( size,  size, size),


        # LEFT

        (-size, -size, -size),
        (-size, -size, size),
        (-size,  size, size),
        (-size,  size, -size),


        # TOP

        (-size, size, size),
        ( size, size, size),
        ( size, size, -size),
        (-size, size, -size),


        # BOTTOM

        (-size, -size, -size),
        ( size, -size, -size),
        ( size, -size, size),
        (-size, -size, size),
    ]


    triangles = []


    for side in range(6):

        start = side * 4


        triangles.append(
            (
                start,
                start + 2,
                start + 1
            )
        )


        triangles.append(
            (
                start,
                start + 3,
                start + 2
            )
        )


    uvs = []


    for side in range(6):

        uvs.extend([

            (0, 0),

            (1, 0),

            (1, 1),

            (0, 1),

        ])


    mesh = Mesh(
        vertices=vertices,
        triangles=triangles,
        uvs=uvs,
        mode='triangle'
    )


    mesh.generate()


    mesh.double_sided = True


    entity = Entity(
        model=mesh,
        texture=SKYBOX_FILE
    )


    entity.double_sided = True


    return entity


skybox = build_skybox()


# ============================================================
# LIGHTING
# ============================================================

sun = DirectionalLight()


sun.look_at(
    Vec3(
        1,
        -1,
        -1
    )
)


ambient = AmbientLight(
    color=color.rgba(
        150,
        150,
        150,
        0.6
    )
)


# ============================================================
# DAY / NIGHT
# ============================================================

world_time = 8.0

DAY_LENGTH = 600.0


def update_day_night():

    global world_time


    world_time += (
        time.dt
        * 24
        / DAY_LENGTH
    )


    if world_time >= 24:

        world_time -= 24


    angle = (
        world_time
        / 24.0
    ) * 360.0


    sun.rotation_x = (
        angle
        - 90
    )


    if (
        world_time >= 6
        and world_time < 18
    ):

        brightness = 1.0

    else:

        brightness = 0.25


    ambient.color = color.rgba(
        int(150 * brightness),
        int(150 * brightness),
        int(150 * brightness),
        0.6
    )


# ============================================================
# START WORLD
# ============================================================

generate_world()

build_world()

# ============================================================
# REBUILD CHUNK
# ============================================================

def rebuild_chunk_at(x, z):

    cx = floor(x / CHUNK_SIZE)
    cz = floor(z / CHUNK_SIZE)

    old_terrain, old_water = chunk_entities.get(
        (cx, cz),
        (None, None)
    )

    if old_terrain:
        destroy(old_terrain)

    if old_water:
        destroy(old_water)

    terrain = build_chunk(cx, cz)
    water = build_water_chunk(cx, cz)

    chunk_entities[(cx, cz)] = (
        terrain,
        water
    )

# ============================================================
# PLAYER SPAWN
# ============================================================

spawn_surface = terrain_heights.get(
    (0, 0),
    WATER_LEVEL
)


player = GigaPlayer()


player.position = (
    0.5,
    spawn_surface + 1.05,
    0.5
)

# ============================================================
# BREAK / PLACE
# ============================================================

def break_block():

    target, previous = raycast_voxel()

    if target is None:
        return

    block = world.get(target, AIR)

    if block == AIR:
        return

    # Don't allow breaking outside the generated world.
    world[target] = AIR


    rebuild_chunk_at(
        target[0],
        target[2]
    )

def place_block():

    target, previous = raycast_voxel()

    if target is None or previous is None:
        return

    x, y, z = previous

    position = (x, y, z)

    if world.get(position, AIR) != AIR:
        return

    block = HOTBAR_BLOCKS[selected_block]

    world[position] = block

    rebuild_chunk_at(
        x,
        z
    )

# ============================================================
# INPUT
# ============================================================
def input(key):


    global selected_block

    if key == 'space':
        player.jump()

    elif key == 'escape':
        mouse.locked = not mouse.locked

    elif key == 'left mouse down':
        break_block()

    elif key == 'right mouse down':
        place_block()

    elif key in ['1', '2', '3', '4', '5', '6']:

        selected_block = int(key) - 1

# ============================================================
# UPDATE
# ============================================================

def update():

    update_day_night()


    # Skybox follows the camera.

    skybox.position = camera.world_position

# ============================================================
# MUSIC
# ============================================================

MUSIC_FILE = 'gigachad.wav'
MUSIC_VOLUME = 0.35

print("Loading music:", MUSIC_FILE)

background_music = Audio(
    MUSIC_FILE,
    loop=True,
    autoplay=False
)

background_music.volume = MUSIC_VOLUME
background_music.play()

print("Music started.")

# ============================================================
# RUN
# ============================================================

app.run()