from deck.panel.hw import ads1115, pca9685, ws2812
from deck.panel.hw.mcp23017 import MCP23017, bit
from tests.fakes import FakeI2C, FakeSPI


def test_pca9685_init_is_open_drain_inverted_and_sets_prescale():
    bus = FakeI2C()
    pca9685.PCA9685(bus, 0x40, freq_hz=1600)
    regs = bus.regs[0x40]
    assert regs[pca9685.MODE2] == pca9685.MODE2_INVRT  # OUTDRV clear: open-drain
    assert not regs[pca9685.MODE2] & 0x04
    assert regs[pca9685.PRESCALE] == 3
    # prescale written while asleep, then woken with auto-increment
    mode1_writes = [w[2][0] for w in bus.writes if w[1] == pca9685.MODE1]
    assert mode1_writes == [pca9685.MODE1_SLEEP, pca9685.MODE1_AUTO_INCREMENT]


def test_pca9685_channel_registers_ends_are_exact():
    assert pca9685.channel_registers(0.0) == [0, 0, 0, pca9685.FULL]
    assert pca9685.channel_registers(1.0) == [0, pca9685.FULL, 0, 0]
    assert pca9685.channel_registers(0.5) == [0, 0, 0x00, 0x08]  # 2048
    assert pca9685.channel_registers(-3) == pca9685.channel_registers(0.0)


def test_pca9685_skips_unchanged_writes():
    bus = FakeI2C()
    chip = pca9685.PCA9685(bus)
    before = len(bus.writes)
    chip.set_sink(9, 0.25)
    chip.set_sink(9, 0.25)
    assert len(bus.writes) == before + 1
    assert bus.writes[-1][1] == pca9685.LED0_ON_L + 4 * 9


def test_mcp23017_configures_inputs_with_pullups_and_reads_active_low():
    bus = FakeI2C()
    chip = MCP23017(bus, 0x20)
    assert bus.regs[0x20][0x00] == 0xFF and bus.regs[0x20][0x01] == 0xFF  # IODIR
    assert bus.regs[0x20][0x0C] == 0xFF and bus.regs[0x20][0x0D] == 0xFF  # GPPU
    bus.regs[0x20][0x12] = 0b1111_1110  # A0 pulled low: closed
    bus.regs[0x20][0x13] = 0b1111_0111  # B3 closed
    pressed = chip.pressed()
    assert pressed == (1 << bit("A", 0)) | (1 << bit("B", 3))


def test_ads1115_config_word_and_scaling():
    word = ads1115.config_word(2)
    assert word >> 15 == 1  # start
    assert (word >> 12) & 0b111 == 0b110  # AIN2 vs GND
    assert (word >> 9) & 0b111 == 0b001  # +-4.096V
    assert ads1115.to_fraction(0) == 0.0
    assert abs(ads1115.to_fraction(round(3.3 / 4.096 * 0x8000)) - 1.0) < 1e-3
    assert ads1115.to_fraction(0xFFF0) == 0.0  # slightly negative reads as zero


def test_ads1115_round_robin_reads_previous_channel_and_starts_next():
    bus = FakeI2C()
    adc = ads1115.ADS1115(bus, 0x48, channels=(0, 1, 2))
    started = lambda: (bus.writes[-1][2][0] << 8 | bus.writes[-1][2][1]) >> 12 & 0b111
    assert started() == 0b100
    bus.regs[0x48][0x00], bus.regs[0x48][0x01] = 0x40, 0x00  # half of +-4.096V
    values = adc.poll()
    assert values[0] is not None and values[1] is None
    assert started() == 0b101


def test_ws2812_encoding_is_grb_three_bits_per_bit_and_capped():
    frame = ws2812.encode([(255, 0, 0)], cap=1.0)
    g, r, b = frame[0:3], frame[3:6], frame[6:9]
    assert g == ws2812._encode_byte(0) and r == ws2812._encode_byte(255) and b == ws2812._encode_byte(0)
    assert ws2812._encode_byte(0xFF) == bytes([0b11011011, 0b01101101, 0b10110110])
    assert frame[9:] == bytes(ws2812.RESET_BYTES)
    capped = ws2812.encode([(255, 255, 255)])  # default 40% power cap
    assert capped[0:3] == ws2812._encode_byte(102)


def test_ws2812_sets_spi_and_skips_identical_frames():
    spi = FakeSPI()
    strip = ws2812.WS2812(spi)
    assert spi.max_speed_hz == ws2812.SPI_HZ and spi.mode == 0
    strip.show([(1, 2, 3)] * 4)
    strip.show([(1, 2, 3)] * 4)
    assert len(spi.frames) == 1
