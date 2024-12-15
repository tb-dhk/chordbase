from hashlib import sha256
import colorsys

def adjust_brightness_saturation(hex_color):
    # Convert hex to RGB
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    # Convert RGB to HSV
    r, g, b = r / 255.0, g / 255.0, b / 255.0  # Normalize RGB to [0, 1]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)

    # Double the brightness and saturation
    s = min(s * 2, 1)  # Saturation can't exceed 1
    v = min(v * 2, 1)  # Value can't exceed 1

    # Convert back to RGB
    r, g, b = colorsys.hsv_to_rgb(h, s, v)

    # Convert back to hex
    r, g, b = int(r * 255), int(g * 255), int(b * 255)
    return f'#{r:02x}{g:02x}{b:02x}'

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

        # Apply the accidental shift and adjust for octave if necessary
        shifted_index = (base_index + accidental_count) % 12
        new_octave = self.octave

        if shifted_index < base_index:
            new_octave += 1  # If the note shifted down, move to the next octave

        enharmonic_note = self.NOTES[shifted_index]

        if letter:
            # Find the letter and adjust accordingly
            letter_index = self.NOTES.index(letter)
            diff = shifted_index - letter_index
            if diff > 6:
                diff -= 12
            elif diff < -6:
                diff += 12

            # Adjust accidentals based on the difference
            if diff > 0:
                enharmonic_note = letter + "#" * diff
            elif diff < 0:
                enharmonic_note = letter + "b" * -diff
        else:
            if favor == "flat" and "#" in enharmonic_note:
                # If flat is favored, prefer flat enharmonic over sharp
                enharmonic_note = self.NOTES[(shifted_index + 1) % 12] + "b"
            if force:
                if favor == "sharp" and enharmonic_note in ["C", "F"]:
                    enharmonic_note = self.NOTES[(shifted_index - 1) % 12] + "#"  # C# and F# for diatonic
                elif favor == "flat" and enharmonic_note in ["B", "E"]:
                    enharmonic_note = self.NOTES[(shifted_index + 1) % 12] + "b"  # Bb and Eb for diatonic
        
        if enharmonic_note == "B#":
            new_octave -= 1
        elif enharmonic_note == "Cb":
            new_octave += 1

        return Note(enharmonic_note, new_octave)

    def __int__(self):
        return self._get_midi_value() 

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
        shifted_index = (base_index + accidental_count)

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
    def str_to_note(cls, string):
        numslice = 0
        while True:
            if string[-numslice-1:].isnumeric():
                numslice -= 1
            else:
                break
        return Note(string[:-numslice], string[-numslice:])

    @classmethod
    def int_to_note(cls, num):
        return Note(cls.NOTES[num % 12], num // 12 - 1)

    def __add__(self, interval):
        letters = "CDEFGAB"
        note = Note.int_to_note(int(self) + int(interval))
        self_index = letters.index(self.letter)
        note = note.enharmonic_equiv(letter=letters[(self_index + interval.number - 1) % 7])
        return note

    def __sub__(self, other):
        """
        Subtract another Note from this one to determine the Interval between them,
        considering both the diatonic (letter) interval and the chromatic (semitone) interval,
        while also accounting for differences in octaves.

        :param other: The other Note to subtract.
        :return: An Interval object representing the difference between the two notes.
        """
        letters = "CDEFGAB"

        # Calculate the diatonic interval without accidentals
        self_no_acc = Note(self.letter, self.octave)
        other_no_acc = Note(other.letter, other.octave)

        self_index = letters.index(self_no_acc.letter)
        other_index = letters.index(other_no_acc.letter)
        diatonic_interval = (self_index - other_index) % 7 + 1  # Diatonic interval (1-7)

        # Chromatic interval calculation (semitones difference)
        chromatic_difference = int(self) - int(other)

        # Account for octave difference
        octave_difference = self.octave - other.octave
        if self_index < other_index:
            octave_difference -= 1
        diatonic_interval += octave_difference * 7

        # Determine quality of the interval
        intervals = [0, 2, 4, 5, 7, 9, 11]  # Major scale semitones
        base_semitones = intervals[(diatonic_interval - 1) % 7] + octave_difference * 12
        quality = chromatic_difference - base_semitones

        # Return the Interval object
        return Interval(diatonic_interval, quality)

    def __eq__(self, other):
        """Check if two notes are equal, based on their chromatic position."""
        return int(self) == int(other)

    def __lt__(self, other):
        """Check if the current note is less than the other note."""
        return int(self) < int(other)

    def __gt__(self, other):
        """Check if the current note is greater than the other note."""
        return int(self) > int(other)

class Interval:
    def __init__(self, number, quality):
        self.number = number
        self.quality = quality
        if self.quality <= -12 or self.quality >= 12:
            self.quality = self.quality % 12

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

    def __eq__(self, other):
        """Check if two notes are equal, based on their chromatic position."""
        return int(self) == int(other)

    def __lt__(self, other):
        """Check if the current note is less than the other note."""
        return int(self) < int(other)

    def __gt__(self, other):
        """Check if the current note is greater than the other note."""
        return int(self) > int(other)

class Chord:
    def __init__(self, *intervals):
        self.intervals = list(intervals) 
        self.intervals.sort(key=lambda x: (x.number, x.quality))

    MAINS = {
        "dim": ["P1", "m3", "D5", "D7", "M9", "P11", "M13"], # dim
        "min": ["P1", "m3", "P5", "m7", "M9", "P11", "M13"], # min
        "dom": ["P1", "M3", "P5", "m7", "M9", "P11", "M13"], # dom
        "maj": ["P1", "M3", "P5", "M7", "M9", "P11", "M13"], # maj
    }

    def notes(self, base=Note("C", 4)):
        notes = [base]
        for i in self.intervals:
            notes.append(base + i)
        return notes

    def quality(self):
        intervals = [str(i) for i in self.intervals]

        if "m3" in intervals:
            if "D5" in intervals and "D7" in intervals:
                quality = "dim"
            else:
                quality = "min"
        elif "M7" in intervals:
            quality = "maj" # dom
        else: 
            quality = "dom"

        return quality

    def sus(self):
        intervals = [str(i) for i in self.intervals]
        if "m3" not in intervals and "M3" not in intervals and "M2" in intervals:
            sus = "sus2"
        elif "M4" in intervals:
            sus = "sus4"
        else:
            sus = ""
        return sus

    def structure(self):
        if [str(i) for i in self.intervals] == ["P5"]:
            return "power"
        notes = max(i.quality for i in self.intervals if i % 2)
        match notes:
            case 1:
                return "unison"
            case 3:
                return "third"
            case 5:
                return "triad"
            case 7:
                return "seventh"
            case 9:
                return "ninth"
            case 11:
                return "eleventh"
            case 13:
                return "thirteenth"

    def name(self, base=None):
        intervals = [str(i) for i in self.intervals]

        # step 1: find the highest note that matches one of these 
        main_number = "1"
        found = False
        for i in range(6, 0, -1):
            for interval in intervals:
                ls = [m[i] for m in Chord.MAINS.values()]
                if interval in ls:
                    main_number = interval[1:]
                    found = True
                    quality = list(Chord.MAINS.keys())[ls.index(interval)]
                    break
            if found:
                break

        additions = []
        sus = ""

        # step 2: decide the main quality
        quality = self.quality()
        sus = self.sus()
        if "M2" in intervals:
            if "M4" in intervals:
                additions.append(Interval(4, 0))

        aug = "A5" in intervals
        if aug:
            main_number = max(aug, 5)

        # step 3: find alterations and additions for odd-numbered tones
        alterations = []
        for interval in intervals:
            number = int(interval[1:])
            # Assume chord_intervals is a list or set of all the intervals currently in the chord
            # Assume the chord quality has already been established

            if number % 2 == 1:  # We're dealing with intervals like 7, 9, 11, etc.
                # Get the expected interval for this position based on the chord quality
                expected_interval = Chord.MAINS[quality][(number // 2) % 7]
                numbers = [i.number for i in self.intervals]

                # Check if the interval has already been added to the chord
                if interval == expected_interval or (interval == "A5" and aug):
                    # This is the main interval, so don't add it again
                    continue  # Move to the next interval (don't process this one again)
                elif numbers.count(number) > 1:
                    # If the same interval has been added already, this is treated as an addition
                    additions.append(Interval.str_to_interval(interval))
                else:
                    # Otherwise, treat it as an alteration
                    alterations.append(Interval.str_to_interval(interval))
            elif number % 2 == 0:
                # If the interval is an even number, and the `sus` string is not the same as the current number, treat as an addition
                if sus[3:] != str(number):
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
        base = base.letter + base.accidental if base else ""
        aug = "aug" if aug else ""
        quality = "" if quality == "dom" else quality
        main_number = "" if int(main_number) in [1, 5] else main_number
        alts = "".join(alts)
        adds = "".join("add" + a for a in adds)
        
        return base + "^"  + aug + sus + quality + main_number + alts + adds

    def inversions(self):
        newints = [self.intervals]

        def cycle(intervals):
            newset = [i for i in intervals] 
            new_octave = (newset[-1].number - 1) // 7 + 1
            newset.append(Interval(7 * new_octave + 1, 0))
            newset = [i - newset[0] for i in newset][1:]
            return newset
        
        for _ in range(len(self.intervals)):
            newints.append(cycle(newints[-1]))
        
        return [Chord(*ints) for ints in newints[1:]] 

    def color(self):
        return adjust_brightness_saturation("#" + sha256(str(self.name()).encode("utf-8")).hexdigest()[:6])

    @classmethod
    def name_to_chord(cls, chord_name):
        """
        Reverse engineers a chord name into a Chord object.
        """
        import re

        # Regex patterns for parsing
        base_pattern = r"^[A-G][#b]*"  # Match the base note (e.g., C, Bb, F#)
        aug_pattern = "aug"
        sus_pattern = r"(sus\d+)"      # Match sus (e.g., sus4, sus2)
        quality_pattern = r"(\^min|\^maj|\^aug|\^dim|\^dom)"  # Match quality
        main_number_pattern = r"(\d+)"  # Match the main number (e.g., 7, 9, 13)
        alteration_pattern = r"([b#♮]\d+)"  # match alterations (e.g., #5, b9)
        addition_pattern = r"add[b#]?\d+"  # match additions (e.g., add9, add#11)

        # Parse base note
        base_match = re.search(base_pattern, chord_name)
        base = base_match.group(0) if base_match else None

        # Parse aug
        aug_match = re.search(aug_pattern, chord_name)
        aug = base_match.group(0) if aug_match else None

        # Parse sus
        sus_match = re.search(sus_pattern, chord_name)
        sus = sus_match.group(1) if sus_match else ""

        # Parse quality
        quality_match = re.search(quality_pattern, chord_name)
        try:
            quality = quality_match.group(1).lstrip("^")
        except:
            quality = "dom"

        # Parse main number
        main_number_match = re.search(main_number_pattern, chord_name)
        main_number = int(main_number_match.group(1)) if main_number_match else 5
        
        # Parse alterations and additions
        alterations = re.findall(alteration_pattern, chord_name)
        additions = re.findall(addition_pattern, chord_name)

        # Convert to intervals
        intervals = []
        existing5 = False
        for i in Chord.MAINS.get(quality, [])[1:(main_number + 1) // 2]:
            if aug and i == "P5":
                existing5 = True
                intervals.append(Interval.str_to_interval("A5"))
            else:
                intervals.append(Interval.str_to_interval(i))
        if aug and not existing5:
            intervals.append(Interval.str_to_interval("A5"))
        if sus:
            intervals.append(Interval.str_to_interval("M"+sus[3:]))

        for add in additions:
            num_sharps = add.count('#')
            num_flats = add.count('b')
            quality = num_sharps - num_flats  # Positive for sharps, negative for flats
            number = int(''.join(filter(str.isdigit, add)))  # Skip the "add" prefix and get the numeric part
            intervals.append(Interval(number, quality))

        for alt in alterations:
            if "add" + alt not in additions:
                num_sharps = alt.count('#')
                num_flats = alt.count('b')
                quality = num_sharps - num_flats  # Positive for sharps, negative for flats
                number = int(''.join(filter(str.isdigit, alt)))  # Extract the numeric part
                intervals.remove(Interval(number, 0))
                intervals.append(Interval(number, quality))

        # Return the reconstructed Chord object
        if base:
            return ChordWithBase(*intervals, base=Note(base, 4) if base else None)
        else:
            return Chord(*intervals)

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "".join(str(i) for i in self.intervals)

class ChordWithBase(Chord):
    def __init__(self, *intervals, base=Note("C", 4)):
        super().__init__(*intervals)
        self.base = base

    def notes(self, base=None):
        if base is None:
            base = self.base
        return super().notes(base=base)

    def name(self, base=None):
        if base is None:
            base = self.base
        return super().name(base=base)

    def inversions(self):
        ls = super().inversions()

        for i in range(len(self.intervals)):
            ls[i] = ChordWithBase(*ls[i].intervals, base=self.notes()[i])

        return ls

    def intervals_between_notes(self):
        dic = {}

        # Use combinations to get pairs of notes
        notes_to_compare = self.notes()
        for i in range(len(notes_to_compare)):
            for j in range(i + 1, len(notes_to_compare)):  # Compare each pair, ensuring no repetitions
                note1 = notes_to_compare[i]
                note2 = notes_to_compare[j]
                
                # Ensure we get the correct interval between notes
                interval = note2 - note1 if note2 > note1 else note1 - note2 

                if interval.number not in dic:
                    dic[interval.number] = []

                # Add the pair to the dictionary under the appropriate interval number
                dic[interval.number].append((note1, note2))

        return dic

    def transpositions(self):
        return [ChordWithBase(*self.intervals, base=Note(n, 4)) for n in Note.NOTES]

    def subchords(self):
        dic = {}
        notes_to_compare = self.notes()

        for i in range(len(notes_to_compare)):
            for j in range(i + 1, len(notes_to_compare)):  # Ensure no repetitions
                note1 = notes_to_compare[i]

                # Collect all notes between note1 and note2 (inclusive)
                notes_in_chord = notes_to_compare[i : j + 1]  # Slice to include notes between

                # Calculate the intervals between the base and each note in the subchord
                base_note = note1  # Set the lowest note as the base
                intervals = [note - base_note for note in notes_in_chord]

                # Create a ChordWithBase object
                chord = ChordWithBase(*intervals[1:], base=base_note)

                # Use the number of the interval between the first and last note as the key
                interval_between_first_and_last = intervals[-1].number

                if interval_between_first_and_last not in dic:
                    dic[interval_between_first_and_last] = []

                # Add the ChordWithBase object to the dictionary
                dic[interval_between_first_and_last].append(chord)

        return dic

    def extensions(self):
        """
        Returns a list of possible Chord objects with extensions based on the chord's quality.
        """
        chord_quality = self.quality()  # Call the quality function
        if chord_quality not in Chord.MAINS:
            return []  # If quality is unrecognized, return an empty list

        # Convert MAINS intervals for the quality into Interval objects
        all_intervals = Chord.MAINS[chord_quality][1:]

        # Determine which intervals are missing
        existing_intervals = set(str(i) for i in self.intervals)
        possible_chords = [self]
        for interval in all_intervals:
            if interval not in existing_intervals:
                # Create a new chord with the additional interval
                new_intervals = possible_chords[-1].intervals + [Interval.str_to_interval(interval)]
                possible_chords.append(ChordWithBase(*new_intervals, base=self.base))

        return possible_chords[1:]

    def simplifications(self):
        """
        Returns a list of possible simplified Chord objects by removing the highest odd scale degree
        until the chord is reduced to a triad.
        """
        odd_intervals = [i for i in self.intervals if i.number % 2 == 1]

        simplifications = []
        current_intervals = self.intervals[:]

        while len(current_intervals) > 1:
            odd_intervals = [i for i in current_intervals if i.number % 2 == 1]
            if not odd_intervals:
                break  # No more odd intervals to remove
            
            # Find the highest odd-numbered interval
            highest_odd = max(odd_intervals, key=lambda x: x.number)

            # Remove the highest odd-numbered interval
            current_intervals = [i for i in current_intervals if i != highest_odd]

            # Create a new simplified chord
            simplified_chord = ChordWithBase(*current_intervals, base=self.base)
            simplifications.append(simplified_chord)

        return simplifications

    def find_matching_scales(self):
        chord_notes = [int(n) % 12 for n in self.notes()]
        scales = {}

        # iterate through each note
        for note in Note.NOTES:
            # iterate through each scale
            for scale in Scale.SCALES:
                fullscale = Scale.generate_scale(scale, base=Note(note, 4))
                scale_notes = [int(n) % 12 for n in fullscale.notes()]
                # check how much of the chord_notes are in scale_notes
                count = len([0 for n in chord_notes if n in scale_notes])
                proportion = count / len(chord_notes)
                if proportion not in scales:
                    scales[proportion] = []
                scales[proportion].append(note + " " + scale)

        return scales

    def __repr__(self):
        return str(self)

    def __str__(self):
        return str(self.base) + " " + str(self.intervals)

class Scale:
    def __init__(self, *intervals, base=Note("C", 4)):
        self.intervals = list(intervals)
        self.intervals.sort(key=lambda x: (x.number, x.quality))
        self.base = base

    SCALES = [
        "major",
        "natural minor", "harmonic minor", "melodic minor",
        "major pentatonic scale", "minor pentatonic scale",
        "blues scale"
    ]

    def notes(self):
        notes = [self.base]
        for i in self.intervals:
            notes.append(self.base + i)
        return notes

    @classmethod
    def generate_scale(cls, name, base=Note("C", 4)):
        scale = Scale(
            *[Interval(i, 0) for i in range(2, 8)],
            base=base
        )
        match name:
            case "major":
                pass
            case "natural minor":
                for i in [1, 4, 5]:
                    scale.intervals[i].quality = -1
            case "harmonic minor":
                for i in [1, 4]:
                    scale.intervals[i].quality = -1
            case "melodic minor":
                scale.intervals[1].quality = -1
            case "major pentatonic scale":
                scale.intervals = [scale.intervals[i] for i in range(len(scale.intervals)) if i not in [2, 5]]
            case "minor pentatonic scale":
                for i in [1, 5]:
                    scale.intervals[i].quality = -1
                scale.intervals = [scale.intervals[i] for i in range(len(scale.intervals)) if i not in [0, 4]]
            case "blues scale":
                for i in [1, 5]:
                    scale.intervals[i].quality = -1
                scale.intervals = [scale.intervals[i] for i in range(len(scale.intervals)) if i not in [0, 4]]
                scale.intervals.append(Interval(4, 1))
                scale.intervals.sort(key=lambda x: (x.number, x.quality))
            case _:
                scale = Scale(base=base)

        return scale

funky = ChordWithBase(
    Interval(3, 0), Interval(5, 0), Interval(7, -1),
    base=Note("C", 4)
)
