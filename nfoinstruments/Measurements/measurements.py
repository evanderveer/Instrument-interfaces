import time

def scan_temp_fixed_biases(measurement_manager, start_temp):
    """
    Perform continuous temperature measurements with fixed biases.

    Args:
        measurement_manager (object): The measurement manager object.
        start_temp (float): The starting temperature for the measurements.
    """
    with open(measurement_manager.filename, "w") as f:
        for bias in measurement_manager.bias_points:
            settle_at_start_temp(measurement_manager, start_temp)
            measurement_manager.lcr.bias = bias
            if measurement_manager.temperature_mode == 'continuous':
                scan_temperature_cont(measurement_manager, f)
            elif measurement_manager.temperature_mode == 'step':
                scan_temperature_step(measurement_manager, f)
            else:
                raise ValueError("invalid temperature mode")

def bias_sweep_temperature_steps(measurement_manager, start_temp):
    """
    Perform continuous temperature measurements with a fixed bias.

    Args:
        measurement_manager (object): The measurement manager object.
        start_temp (float): The starting temperature for the measurements.
    """
    settle_at_start_temp(measurement_manager, start_temp)
    with open(measurement_manager.filename, "w") as f:
        for T_point in measurement_manager.temperature_points:
            measurement_manager.ppms.temperature_setpoint = T_point
            while True:
                time.sleep(5)
                if measurement_manager.ppms.temperature_stable:
                    break
            time.sleep(measurement_manager.settle_time)
            scan_bias(measurement_manager, f)
            
def freq_sweep_temperature_steps_bias_steps(measurement_manager, start_temp):
    """
    Perform frequency-dependent measurements with fixed temperature steps.

    Args:
        measurement_manager (object): The measurement manager object.
        start_temp (float): The starting temperature for the measurements.
    """
    settle_at_start_temp(measurement_manager, start_temp)
    with open(measurement_manager.filename, "w") as f:
        for T_point in measurement_manager.temperature_points:
            print('\n', flush=True)
            print(f'Changing temperature to {T_point} K.', flush=True)
            for b_point in measurement_manager.bias_points:
                print(f'Setting bias to {b_point} V.', flush=True)
                measurement_manager.ppms.temperature_setpoint = T_point
                measurement_manager.lcr.bias = b_point 
                time.sleep(0.1)
                while True:
                    time.sleep(5)
                    if measurement_manager.ppms.temperature_stable:
                        break
                time.sleep(measurement_manager.settle_time)
                scan_frequency(measurement_manager, f)
            
def scan_frequency(measurement_manager, f, no_ppms=False):
    """
    Perform a scan of the frequency.

    Args:
        measurement_manager (object): The measurement manager object.
        f (file): The file object for writing measurement data.
    """
    for frequency in measurement_manager.frequency_points:
        measurement_manager.lcr.frequency = frequency
        time.sleep(0.1)
        write_measurement_data(f, measurement_manager, no_ppms=no_ppms)            

def scan_bias(measurement_manager, f):
    """
    Perform a scan of the bias.

    Args:
        measurement_manager (object): The measurement manager object.
        f (file): The file object for writing measurement data.
    """
    for bias in measurement_manager.bias_points:
        measurement_manager.lcr.bias = bias 
        time.sleep(0.1)
        write_measurement_data(f, measurement_manager)

def scan_temperature_cont(measurement_manager, f):
    """
    Perform continuous temperature scanning.

    Args:
        measurement_manager (object): The measurement manager object.
        f (file): The file object for writing measurement data.
    """
    for T_point in measurement_manager.temperature_points:
        
        measurement_manager.ppms.temperature_setpoint = T_point
        time.sleep(1)
        while True:
            write_measurement_data(f, measurement_manager)
            if abs(measurement_manager.ppms.temperature -
                   measurement_manager.ppms.temperature_setpoint[0]) < 0.5:
                break

def scan_temperature_step(measurement_manager, f):
    """
    Perform step-based temperature scanning.

    Args:
        measurement_manager (object): The measurement manager object.
        f (file): The file object for writing measurement data.
    """
    for T_point in measurement_manager.temperature_points:
        measurement_manager.ppms.temperature_setpoint = T_point
        while True:
            time.sleep(5)
            if measurement_manager.ppms.temperature_stable:
                break
        time.sleep(measurement_manager.settle_time)
        write_measurement_data(f, measurement_manager)

def write_measurement_data(f, measurement_manager, no_ppms=False):
    """
    Write measurement data to the file.

    Args:
        f (file): The file object for writing measurement data.
        measurement_manager (object): The measurement manager object.
    """
    for i in range(5):
        try:
            cap_res = measurement_manager.lcr.get_value()
        except:
            continue
        else:
            break
    else:
        return
    if no_ppms:
        curr_temperature = -1
    else: 
        curr_temperature = measurement_manager.ppms.temperature
    data_string = ','.join([str(time.time()), 
                            str(measurement_manager.lcr.bias), 
                            str(measurement_manager.lcr.frequency),
                            str(curr_temperature),
                            str(cap_res[0]),
                            str(cap_res[1]),
                            '\n',
                            ])
    f.write(data_string)

def settle_at_start_temp(measurement_manager, start_temp):
    """
    Settle at the starting temperature.

    Args:
        measurement_manager (object): The measurement manager object.
        start_temp (float): The starting temperature.
    """
    measurement_manager.ppms.temperature_setpoint = (start_temp, 10, 0)
    while True:
        time.sleep(5)
        if measurement_manager.ppms.temperature_stable:
            break