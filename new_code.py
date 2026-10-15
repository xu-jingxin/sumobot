# =====================================
# EV3 SUMO ROBOT - IMPROVED VERSION
# =====================================

left = ev3_motorA()
right = ev3_motorD()

ultrasonic = ev3_ultrasonicSensor()
color = ev3_colorSensor()

# =====================================
# SETTINGS
# =====================================

MATCH_TIME = 60

DETECT_DISTANCE = 40
PUSH_DISTANCE = 12

CRUISE_SPEED = 650
CHARGE_SPEED = 1000
RUN_SPEED = 500
TURN_SPEED = 800

# Milliseconds
STEP = 50
COMMAND_TIME = 110

# Seconds
EDGE_FORWARD_TIME = 0.45
EDGE_TURN_TIME = 0.55
CHARGE_TIME = 0.65
PUSH_TIME = 0.35
RUN_TIME = 0.25

ATTACK_COOLDOWN = 1.0

# Change to True when testing on a white table.
# No boundary protection in test mode.
WHITE_TABLE_TEST = False


# =====================================
# MOVEMENT
# =====================================

def drive(left_speed, right_speed):
    ev3_runForTime(
        left, COMMAND_TIME, left_speed
    )
    ev3_runForTime(
        right, COMMAND_TIME, right_speed
    )

    ev3_pause(STEP)


# =====================================
# COLOUR SENSOR
# =====================================

def near_edge():
    if WHITE_TABLE_TEST:
        return False

    c = ev3_colorSensorGetColor(color)

    # Actual outer boundary is white (6).
    # Yellow (4) is an early warning.
    # Red (5) may also be the purple centre,
    # so don't treat every 5 as an edge.
    return c == 4 or c == 6


# =====================================
# MAIN PROGRAM
# =====================================

start = time_time()

state = "start"
until = start + 0.6

direction = 1
last_edge = start - 5
last_attack = start - 5

print("SUMO STARTED")


while time_time() - start < MATCH_TIME:

    now = time_time()

    distance = ev3_ultrasonicSensorDistance(
        ultrasonic
    )

    edge = near_edge()

    # =================================
    # PRIORITY 1: EDGE DETECTION
    # =================================

    # Edge detection interrupts everything,
    # including charging and retreating.
    if edge and state != "edge":
        print("EDGE!")

        state = "edge"
        until = now + EDGE_FORWARD_TIME

        last_edge = now

    # =================================
    # START: MOVE INTO ARENA
    # =================================

    if state == "start":

        drive(450, 450)

        if now >= until:
            state = "circle"

    # =================================
    # EDGE: MOVE AWAY FROM REAR EDGE
    # =================================

    elif state == "edge":

        # The colour sensor is at the rear.
        # Forward motion moves away from it.
        drive(650, 650)

        # Do not finish recovery while
        # the sensor still sees danger.
        if not edge and now >= until:
            state = "turn"
            until = now + EDGE_TURN_TIME

    # =================================
    # TURN: CHANGE HEADING
    # =================================

    elif state == "turn":

        drive(
            direction * TURN_SPEED,
            -direction * TURN_SPEED
        )

        if now >= until:
            state = "circle"
            direction = -direction

    # =================================
    # CHARGE: FIXED SHOVEL ATTACK
    # =================================

    elif state == "charge":

        drive(CHARGE_SPEED, CHARGE_SPEED)

        if distance > 0 and distance < PUSH_DISTANCE:
            state = "push"
            until = now + PUSH_TIME

        elif now >= until:
            state = "run"
            until = now + RUN_TIME

    # =================================
    # PUSH: CONTINUE FOR SHORT BURST
    # =================================

    elif state == "push":

        drive(CHARGE_SPEED, CHARGE_SPEED)

        if now >= until:
            state = "run"
            until = now + RUN_TIME

    # =================================
    # RUN: SHORT RETREAT
    # =================================

    elif state == "run":

        # Keep retreat short so the rear
        # sensor can detect danger.
        drive(-RUN_SPEED, -RUN_SPEED)

        if now >= until:
            state = "circle"

    # =================================
    # CIRCLE: SEARCH FOR OPPONENT
    # =================================

    else:

        if (distance > 0 and
            distance < DETECT_DISTANCE and
            now - last_attack > ATTACK_COOLDOWN and
            now - last_edge > 1.0):

            print("CHARGE!")

            state = "charge"
            until = now + CHARGE_TIME
            last_attack = now

            drive(CHARGE_SPEED, CHARGE_SPEED)

        else:
            # Backward circular patrol.
            # Rear colour sensor leads.
            drive(
                -CRUISE_SPEED,
                -CRUISE_SPEED - 180
            )


# =====================================
# END
# =====================================

ev3_motorStop(left)
ev3_motorStop(right)

print("MATCH FINISHED")
