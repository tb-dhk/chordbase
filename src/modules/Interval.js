import Note from './Note'

export default class Interval {
    constructor(number, quality) {
        this.number = number;
        this.quality = quality;
        if (this.quality <= -12 || this.quality >= 12) {
            this.quality = this.quality % 12;
        }
    }

    name() {
        let ordinal = ["st", "nd", "rd"][(this.number % 10) - 1] || "th";
        let name;
        
        if (this.quality === 1) {
            name = "augmented";
        } else if ([1, 4, 5].includes(this.number % 7)) {
            name = this.quality === -1 ? "diminished" : "perfect";
        } else {
            name = {
                "-2": "diminished",
                "-1": "minor",
                "0": "major"
            }[this.quality] || "major";
        }
        return `${name} ${this.number}${ordinal}`;
    }

    toString() {
        let name;
        
        if (this.quality === 1) {
            name = "A";
        } else if ([1, 4, 5].includes(this.number % 7)) {
            name = this.quality === -1 ? "D" : "P";
        } else {
            name = {
                "-2": "D",
                "-1": "m",
                "0": "M"
            }[this.quality] || "M";
        }
        return `${name}${this.number}`;
    } 

    static strToInterval(intervalStr) {
        /**
         * Parse a string representation of an interval into an Interval object.
         * 
         * @param {string} intervalStr - A string like 'M3', 'P5', 'A4', 'D7'.
         * @return {Interval} The corresponding Interval object.
         */
        const qualityChar = intervalStr[0];
        const number = parseInt(intervalStr.slice(1), 10);

        let quality;
        if ([1, 4, 5].includes(number % 7)) {  // Perfect intervals (1, 4, 5, +7n)
            const qualityMap = {
                'P': 0,   // Perfect
                'A': 1,   // Augmented
                'D': -1   // Diminished for perfect intervals (-2 otherwise)
            };
            quality = qualityMap[qualityChar] || 0;
        } else {  // Major/minor intervals (2, 3, 6, 7, +7n)
            const qualityMap = {
                'M': 0,   // Major
                'm': -1,  // Minor
                'A': 1,   // Augmented
                'D': -2   // Diminished for perfect intervals (-2 otherwise)
            };
            quality = qualityMap[qualityChar] || 0;
        }

        return new Interval(number, quality);
    }

    // Helper method to convert interval to semitones
    toSemitones() {
        // Assuming this returns the semitone value of the interval, you can define it here
        // Example: a Major 3rd would return 4 semitones
        const intervals = [0, 2, 4, 5, 7, 9, 11]; // Just a placeholder
        return intervals[(this.number - 1) % 7] + this.quality + Math.floor((this.number - 1) / 7) * 12;
    }

    // Addition of two intervals
    add(other) {
        const intervals = [0, 2, 4, 5, 7, 9, 11];
        const newNumber = this.number + other.number - 1;
        const semitones = this.toSemitones() + other.toSemitones();
        let newQuality = semitones - intervals[(newNumber - 1) % 7];

        // Normalize quality to within the range [-6, 6]
        if (newQuality > 6) newQuality -= 12;
        else if (newQuality < -6) newQuality += 12;

        return new Interval(newNumber, newQuality);
    }

    // Subtraction of two intervals
    subtract(other) {
        const intervals = [0, 2, 4, 5, 7, 9, 11];
        const newNumber = this.number + 1 - other.number;
        const semitones = this.toSemitones() - other.toSemitones();
        let newQuality = semitones - intervals[(newNumber - 1) % 7];

        // Normalize quality to within the range [-6, 6]
        if (newQuality > 6) newQuality -= 12;
        else if (newQuality < -6) newQuality += 12;

        return new Interval(newNumber, newQuality);
    }

    // Helper method to convert semitones back to note (enharmonic equivalence handled)
    intToNote(semitones) {
        const notes = [
            "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"
        ];
        const octave = Math.floor(semitones / 12);
        const letter = notes[semitones % 12];

        return new Note(letter, octave);
    }
}
