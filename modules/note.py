class Note:
    # List of note names in ascending order (from C upwards)
    NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

    def __init__(self, name: str, octave: int):
        """
        Initialize a musical note with its full name and octave.
        
        :param name: The full name of the note (e.g., 'A', 'C#', 'Dbb').
        :param octave: The octave of the note (e.g., 4 for A4).
        """
        self.letter = name[0]  # The letter name (e.g., 'A')
        self.accidental = name[1:]  # Accidentals, if any (e.g., '#', 'b', '##', 'bb')
        self.octave = octave

    @property
    def midi(self):
        return self._get_midi_value()

    @property
    def frequency(self):
        return self._get_frequency()

    def enharmonic_equiv(self, favor="natural", force=False, letter=""):
        """
        Return the enharmonic equivalent of the note as a new Note object.
        
        :param favor: If "sharp", favor sharp enharmonics (e.g., A# -> Bb), 
                      If "flat", favor flat enharmonics (e.g., D# -> C#).
                      If "natural", minimize accidentals (e.g., A# -> A, D# -> D).
        :param force: If True, force certain notes to take a sharp or flat, even if it
                      would be naturally notated differently.
        :return: A new Note object representing the enharmonic equivalent.
        """
        base_note = self.letter
        accidental_count = self.accidental.count('#') - self.accidental.count('b')

        # Calculate the base index in the NOTES list
        base_index = self.NOTES.index(base_note)

        # Apply the accidental shift
        shifted_index = (base_index + accidental_count) % 12

        enharmonic_note = self.NOTES[shifted_index]

        if letter:
            # find the letter
            letter_index = self.NOTES.index(letter)

            # find letter - shifted_index
            diff = shifted_index - letter_index
            if diff > 6:
                diff -= 12
            elif diff < -6:
                diff += 12

            # if it's positive, #
            if diff > 0:
                enharmonic_note = letter + "#" * diff

            # else, -
            elif diff < 0:
                enharmonic_note = letter + "b" * -diff
        else:
            if favor == "flat":
                # If flat is favored, make it flat, prefer flat over sharp
                if "#" in enharmonic_note:  # If it's sharp, make it flat
                    enharmonic_note = self.NOTES[(shifted_index + 1) % 12] + "b"

            # Force Logic for "sharp" and "flat" when certain notes (like B, E, etc.) need forced accidentals
            if force:
                if favor == "sharp" and enharmonic_note in ["C", "F"]:
                    enharmonic_note = self.NOTES[(shifted_index - 1) % 12] + "#"  # C# and F# for diatonic
                elif favor == "flat" and enharmonic_note in ["B", "E"]:
                    enharmonic_note = self.NOTES[(shifted_index + 1) % 12] + "b"  # Bb and Eb for diatonic

        return Note(enharmonic_note, self.octave)

    def __int__(self):
        return self._get_midi_value() - 60

    def _get_midi_value(self):
        """
        Calculate the MIDI value of the note based on the enharmonic equivalent.
        
        :return: MIDI value (integer) for the note.
        """
        # Calculate the base note index in the NOTES list
        base_note = self.letter
        accidental_count = self.accidental.count('#') - self.accidental.count('b')
        base_index = self.NOTES.index(base_note)

        # Apply the accidental shift
        shifted_index = (base_index + accidental_count) % 12
        if shifted_index < 0:
            shifted_index += 12

        # The MIDI value of C4 is 60, so calculate based on that
        midi_value = 12 * (self.octave + 1) + shifted_index
        return midi_value

    def _get_frequency(self):
        """
        Calculate the frequency of the note using the standard equal-tempered scale,
        where A4 is 440 Hz.
        
        :return: The frequency of the note in Hertz.
        """
        frequency = 440 * (2 ** ((self.midi - 69) / 12))
        return frequency

    def __repr__(self):
        return str(self)

    def __str__(self):
        """
        Return a string representation of the note (e.g., 'A4').
        """
        return f'{self.letter}{self.accidental}{self.octave}'

    @classmethod
    def int_to_note(cls, num):
        return Note(cls.NOTES[num % 12], num // 12 + 4)

    def __add__(self, interval):
        letters = "ABCDEFG"
        note = Note.int_to_note(int(self) + int(interval))
        self_index = letters.index(self.letter)
        note = note.enharmonic_equiv(letter=letters[(self_index + interval.number - 1) % 7])
        return note

class Interval:
    def __init__(self, number, quality):
        self.number = number
        self.quality = quality

    def name(self):
        if self.number % 10 in [1, 2, 3] and self.number // 10 != 1:
            ordinal = ["st", "nd", "rd"][self.number % 10 - 1]
        else:
            ordinal = "th"

        if self.quality == 1:
            name = "augmented"
        elif self.number % 7 in [1, 4, 5]:
            if self.quality == -1:
                name = "diminished"
            elif self.quality == 0:
                name = "perfect"
        else:
            if self.quality == -2:
                name = "diminished"
            elif self.quality == -1:
                name = "minor"
            elif self.quality == 0:
                name = "major"

        return f"{name} {self.number}{ordinal}"

    @classmethod
    def str_to_interval(cls, interval_str):
        """
        Parse a string representation of an interval into an Interval object.
        :param interval_str: A string like 'M3', 'P5', 'A4', 'D7'.
        :return: An Interval object.
        """
        # Map the quality to numerical values
        quality_map = {
            'M': 0,   # Major
            'm': -1,  # Minor
            'P': 0,   # Perfect
            'A': 1,   # Augmented
            'D': -1   # Diminished for perfect intervals (-2 otherwise)
        }

        # Extract quality and number
        quality_char = interval_str[0]
        if quality_char in "pad":
            quality_char = quality_char.upper()

        number = int(interval_str[1:])

        # Determine if the interval is perfect or major/minor
        if number % 7 in [1, 4, 5]:  # Perfect intervals (1, 4, 5, +7n)
            if quality_char == 'D':
                quality = -1  # Diminished for perfect intervals is -1
            else:
                quality = quality_map[quality_char]
        else:  # Major/minor intervals (2, 3, 6, 7, +7n)
            if quality_char == 'D':
                quality = -2  # Diminished for major/minor intervals is -2
            else:
                quality = quality_map[quality_char]

        return Interval(number, quality)

    def __int__(self):
        intervals = [0, 2, 4, 5, 7, 9, 11]
        num = self.number - 1
        return num // 7 * 12 + intervals[num % 7] + self.quality

    def __add__(self, other):
        # Adding two intervals
        intervals = [0, 2, 4, 5, 7, 9, 11]
        new_number = self.number + other.number - 1
        semitones = int(self) + int(other)
        new_quality = semitones - intervals[(new_number - 1) % 7]
        if new_quality > 6:
            new_quality -= 12
        elif new_quality < -6:
            new_quality += 12
        
        return Interval(new_number, new_quality)

    def __sub__(self, other):
        # Adding two intervals
        intervals = [0, 2, 4, 5, 7, 9, 11]
        new_number = self.number + 1 - other.number
        semitones = int(self) - int(other)
        new_quality = semitones - intervals[(new_number - 1) % 7]
        if new_quality > 6:
            new_quality -= 12
        elif new_quality < -6:
            new_quality += 12

        return Interval(new_number, new_quality)

    def __repr__(self):
        return str(self)

    def __str__(self):
        name = self.name()
        return (name[0].upper() if name[:2] != "mi" else name[0]) + name.split()[-1][:-2]

class Chord:
    def __init__(self, *intervals):
        self.intervals = list(intervals) 
        self.intervals.sort(key=lambda x: x.number)

    def notes(self, starting):
        notes = [starting]
        for i in self.intervals:
            notes.append(starting + i)
        return str(notes)

    def name(self, starting=None):
        intervals = [str(i) for i in self.intervals]

        # step 1: find the highest note that matches one of these
        mains = {
            "maj": ["P1", "M3", "P5", "M7", "M9", "M11", "M13"], # maj
            "dom": ["P1", "M3", "P5", "m7", "M9", "M11", "M13"], # dom
            "min": ["P1", "m3", "P5", "m7", "M9", "M11", "M13"], # min
            "dim": ["P1", "m3", "D5", "D7", "M9", "M11", "M13"], # dim
        }
        
        main_number = "1"
        found = False
        for i in range(5, -1, -1):
            for interval in intervals:
                if interval in [m[i] for m in mains.values()]:
                    main_number = interval[1:]
                    found = True
                    break
            if found:
                break

        additions = []
        sus = ""

        # step 2: decide the main quality
        if "m3" not in intervals and "M3" not in intervals and (
            "M2" in intervals or "M4" in intervals
        ):
            if "M2" in intervals:
                if "M4" in intervals:
                    additions.append(Interval(4, 0))
                sus = "sus2"
            else:
                sus = "sus4"
        if "m3" in intervals:
            if "m5" in intervals or "D7" in intervals:
                quality = "dim"
            else:
                quality = "min"
        elif "M7" in intervals:
            quality = "maj" # dom
        else: 
            quality = "dom"

        # step 3: find alterations and additions for odd-numbered tones
        alterations = []
        for interval in intervals:
            number = int(interval[1:])
            if number % 2 == 1 and interval != mains[quality][(number // 2) % 7]:
                alterations.append(Interval.str_to_interval(interval))
            elif number % 2 == 0 and sus[3:] != str(number):
                additions.append(Interval.str_to_interval(interval))

        alts = []
        for alt in alterations:
            num = alt.number
            qual = alt.quality
            alt = ("#" * qual if qual > 0 else ("b" * -qual if qual < 0 else "♮")) + str(num) 
            alts.append(alt)

        adds = []
        for add in additions:
            num = add.number
            qual = add.quality
            add = ("#" * qual if qual > 0 else ("b" * -qual if qual < 0 else "")) + str(num) 
            adds.append(add)

        # step 4: assemble!
        starter = starting if starting else ""
        quality = "" if quality == "dom" else quality
        main_number = "" if main_number == "1" else main_number
        alts = "".join(alts)
        adds = "".join("add" + a for a in adds)
        return starter + sus + "^" + quality + main_number + " " + alts + " " + adds

    def inversions(self):
        newints = [self.intervals]

        def cycle(intervals):
            newints = intervals
            new_octave = (newints[-1].number - 1) // 7 + 1
            newints.append(Interval(7 * new_octave + 1, 0))
            newints = [i - newints[0] for i in newints][1:]
            return newints
        
        for _ in range(len(self.intervals)):
            newints.append(cycle(newints[-1]))
        
        return [Chord(*ints) for ints in newints] 

    def __str__(self):
        return str(self.intervals)
