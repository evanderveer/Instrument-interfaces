#Move all of this into the Measurement class
self._filename = None
self._temperature_continuous = True
self._temperature_points = None
self._settle_time = 0
self._bias_points = None
self._frequency_points = None

@property
def temperature_mode(self):
    """
    Get the temperature mode.

    Returns:
        str: The temperature mode ('continuous' or 'step').
    """
    
    if self._temperature_continuous == True:
        return 'continuous'
    return 'step'

@temperature_mode.setter
def temperature_mode(self, mode):
    """
    Set the temperature mode.

    Args:
        mode (str): The temperature mode ('continuous' or 'step').

    Raises:
        ValueError: If the mode is not 'continuous' or 'step'.
    """

    if not mode in ['continuous', 'step']:
        raise ValueError("temperature mode must be 'continuous' or 'step'")
    if mode == 'continuous':
        self._temperature_continuous = True
    else:
        self._temperature_continuous = False

@property
def temperature_points(self):
    """
    Get the temperature points.

    Returns:
        tuple: A tuple of tuples representing the temperature points.
    """

    return self._temperature_points

@temperature_points.setter
def temperature_points(self, points):
    """
    Set the temperature points.

    Args:
        points (tuple): A tuple of tuples representing the temperature points.

    Raises:
        ValueError: If the points format is invalid or the values are out of range.
    """

    if not type(points) is tuple:
        raise ValueError("temperature points must be a tuple of tuples (temperature, rate, approach mode)")
    if any((not (type(i) is tuple)) for i in points):
        raise ValueError("temperature points must be a tuple of tuples (temperature, rate, approach mode)")
    if any(i[0]<2 or i[0]>400 for i in points):
        raise ValueError("one or more of the temperature points exceeds the minimum or maximum temperature")
    if any(i[1]<=0 or i[1]>20 for i in points):
        raise ValueError("one or more of the rates exceeds the minimum or maximum value") 
    if not all(i[2] in ['fast settle', 'no overshoot'] for i in points):
        raise ValueError("all approach modes must be either 'fast settle' or 'no overshoot'") 
    self._temperature_points = points

@property
def bias_points(self):
    """
    Get the bias points.

    Returns:
        tuple: A tuple of biases representing the bias points.
    """

    return self._bias_points

@bias_points.setter
def bias_points(self, points):
    """
    Set the bias points.

    Args:
        points (iterable): An iterable (list, tuple) of biases representing the bias points.

    Raises:
        ValueError: If the points format is invalid or the values are out of range.
    """

    if not hasattr(points, "__iter__"):
        raise ValueError("bias points must be an iterable (list, tuple) of temperatures")
    points = tuple(points) # In case a generator is passed
    if any(i<0 or i>40 for i in points):
        raise ValueError("one or more of the bias points exceeds the minimum or maximum bias") 
    self._bias_points = points
    
@property
def frequency_points(self):
    """
    Get the frequency points.

    Returns:
        tuple: A tuple of biases representing the frequency points.
    """

    return self._frequency_points

@frequency_points.setter
def frequency_points(self, points):
    """
    Set the frequency points.

    Args:
        points (iterable): An iterable (list, tuple) of biases representing the frequency points.

    Raises:
        ValueError: If the points format is invalid or the values are out of range.
    """

    if not hasattr(points, "__iter__"):
        raise ValueError("frequency points must be an iterable (list, tuple) of temperatures")
    points = tuple(points) # In case a generator is passed
    if any(i<20 or i>2_000_000 for i in points):
        raise ValueError("one or more of the frequency points exceeds the minimum or maximum") 
    self._frequency_points = points
    
@property
def settle_time(self):
    """
    Get the settle time.

    Returns:
        float: The settle time value.
    """

    return self._settle_time

@settle_time.setter
def settle_time(self, time):
    """
    Set the settle time.

    Args:
        time (float): The settle time value.

    Raises:
        ValueError: If the time value is invalid.
    """

    if (not (type(time) == int or type(time) == float)) or time < 0:
        raise ValueError("settle time must be a number > 0")
    if self._temperature_continuous == True:
        print("settle time will be ignored in continuous temperature mode")
    self._settle_time = time