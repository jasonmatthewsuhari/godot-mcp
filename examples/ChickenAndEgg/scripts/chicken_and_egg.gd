extends Node3D

const CYCLE_LENGTH := 3.2
const LAY_TRIGGER_TIME := 1.8
const CROUCH_START := 1.45
const CROUCH_END := 2.35
const GROUND_Y := 0.18

@onready var chicken: Node3D = $Chicken
@onready var wing_left: Node3D = $Chicken/WingLeft
@onready var wing_right: Node3D = $Chicken/WingRight
@onready var egg: Node3D = $Egg

var _time := 0.0
var _egg_velocity := 0.0
var _egg_active := false

func _ready() -> void:
	_reset_egg()

func _process(delta: float) -> void:
	var previous_cycle_t := fmod(_time, CYCLE_LENGTH)
	_time += delta
	var cycle_t := fmod(_time, CYCLE_LENGTH)

	if _crossed_time(previous_cycle_t, cycle_t, LAY_TRIGGER_TIME):
		_spawn_egg()

	_animate_chicken(cycle_t)
	_update_egg(delta)

func _animate_chicken(cycle_t: float) -> void:
	var crouch := 0.0
	if cycle_t >= CROUCH_START and cycle_t <= CROUCH_END:
		var p := (cycle_t - CROUCH_START) / (CROUCH_END - CROUCH_START)
		crouch = sin(p * PI)

	var bob := sin(_time * 5.0) * 0.02
	chicken.position.y = 1.0 - (crouch * 0.22) + bob
	chicken.rotation_degrees.x = -8.0 * crouch

	var flap := sin(_time * 10.0) * 22.0
	wing_left.rotation_degrees.z = 22.0 + flap
	wing_right.rotation_degrees.z = -22.0 - flap

func _spawn_egg() -> void:
	egg.visible = true
	egg.position = chicken.position + Vector3(-0.02, -0.58, 0.13)
	_egg_velocity = -0.15
	_egg_active = true

func _update_egg(delta: float) -> void:
	if not _egg_active:
		return

	_egg_velocity += 6.5 * delta
	egg.position.y -= _egg_velocity * delta

	if egg.position.y <= GROUND_Y:
		egg.position.y = GROUND_Y
		if _egg_velocity > 0.55:
			_egg_velocity = -_egg_velocity * 0.35
		else:
			_egg_velocity = 0.0
			_egg_active = false

func _reset_egg() -> void:
	egg.visible = false
	egg.position = Vector3(0.0, GROUND_Y, 0.0)
	_egg_velocity = 0.0
	_egg_active = false

func _crossed_time(previous_t: float, current_t: float, target_t: float) -> bool:
	if previous_t <= current_t:
		return previous_t < target_t and current_t >= target_t
	return previous_t < target_t or current_t >= target_t
