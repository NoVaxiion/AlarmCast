# Hardware/System Architecture

The hardware of the device consists of a Raspberry Pi with wi-fi capabilities connected to a microphone. 

The microphone takes in audio for the device to process, determining if the given audio is a potential alarm or not. This preemptive screening will be done on the Raspberry Pi itself, and if determined to be a potential alarm, a stream of audio will be sent to the backend for more accurate computation. 

This stream of audio requires internet connection, hence the wi-fi capabilities of the Pi.

As the backend recieves the data and request to compute, it will query the database, gathering the alarm fingerprint for a given user, and the given users contacts. 

If determined to be an alarm with a significant degree of accuracy, the given users contacts as well as the user will be notified. However, if no alarm is detected, zero action will be taken.