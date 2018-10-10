from unittest import mock
import pytest

from brain import MarvinBrain


@pytest.fixture
def test_ip():
    return '127.0.0.1'


@pytest.fixture
def marvin(test_ip):
    return MarvinBrain(test_ip)


@pytest.fixture
def marvin_mocked(marvin):
    marvin._do_request = mock.Mock()
    return marvin


def test_marvin_init_attributes(marvin, test_ip):
    assert marvin._ip == test_ip
    assert marvin.all_steps == 0


def test_marvin_url_led_property(marvin, test_ip):
    assert marvin.url_led == f'{test_ip}/led/'


def test_marvin_url_servo_property(marvin, test_ip):
    assert marvin.url_servo == f'{test_ip}/servoR/value?'


def test_marvin_url_stepper_property(marvin, test_ip):
    assert marvin.url_stepper == f'{test_ip}/stepper/'


@mock.patch('brain.urlopen')
def test_marvin_do_request(urlopen_mocked, marvin):
    expected_url_call = 'test.com/test'
    marvin._do_request(expected_url_call)
    urlopen_mocked.assert_called_with(expected_url_call)


def test_marvin_turn_led(marvin_mocked):
    state = 'stateON'
    marvin_mocked._turn_led(state)
    marvin_mocked._do_request.assert_called_with(marvin_mocked.url_led + state)


def test_marvin_turn_led_on(marvin_mocked):
    marvin_mocked.turn_led_on()
    marvin_mocked._do_request.assert_called_with(marvin_mocked.url_led + MarvinBrain.LED_STATE_ON)


def test_marvin_turn_led_off(marvin_mocked):
    marvin_mocked.turn_led_off()
    marvin_mocked._do_request.assert_called_with(marvin_mocked.url_led + MarvinBrain.LED_STATE_OFF)


def test_marvin_move_servo(marvin_mocked):
    angle = 90
    marvin_mocked.move_servo(angle)
    marvin_mocked._do_request.assert_called_with(marvin_mocked.url_servo + str(angle))


def test_marvin_move_servo_lower_than_0(marvin_mocked):
    angle = -10
    marvin_mocked.move_servo(angle)
    marvin_mocked._do_request.assert_called_with(marvin_mocked.url_servo + str(0))


def test_marvin_move_servo_lower_than_0_but_90(marvin_mocked):
    angle = -90
    marvin_mocked.move_servo(angle)
    marvin_mocked._do_request.assert_called_with(marvin_mocked.url_servo + str(-90))


def test_marvin_move_servo_greater_than_90(marvin_mocked):
    angle = 1000
    marvin_mocked.move_servo(angle)
    marvin_mocked._do_request.assert_called_with(marvin_mocked.url_servo + str(90))
