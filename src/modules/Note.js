import Interval from './Interval'

export default class Note {
  // List of note names in ascending order (from C upwards)
  static NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];

  constructor(name, octave) {
    /**
     * Initialize a musical note with its full name and octave.
     * 
     * @param {string} name - The full name of the note (e.g., 'A', 'C#', 'Dbb').
     * @param {number} octave - The octave of the note (e.g., 4 for A4).
     */
    this.letter = name[0];  // The letter name (e.g., 'A')
    this.accidental = name.slice(1);  // Accidentals, if any (e.g., '#', 'b', '##', 'bb')
    this.octave = octave;
  }

  get midi() {
    return this._getMidiValue();
  }

  get frequency() {
    return this._getFrequency();
  }

  toString() {
    return this.letter + this.accidental + this.octave
  }

  enharmonicEquiv() {
    /**
     * Return the enharmonic equivalent of the note as a new Note object.
     * 
     * @param {string} favor - If "sharp", favor sharp enharmonics (e.g., A# -> Bb), 
     *              If "flat", favor flat enharmonics (e.g., D# -> C#).
     *              If "natural", minimize accidentals (e.g., A# -> A, D# -> D).
     * @param {boolean} force - If True, force certain notes to take a sharp or flat, even if it
     *               would be naturally notated differently.
     * @return {Note} A new Note object representing the enharmonic equivalent.
     */
    let favor = "natural"
    let force = false
    let letter = ""
    
    if (arguments[0]) {
      favor = arguments[0].favor
      force = arguments[0].force
      letter = arguments[0].letter
    } 

    let baseNote = this.letter;
    let accidentalCount = (this.accidental.match(/#/g) || []).length - (this.accidental.match(/b/g) || []).length;

    // Calculate the base index in the NOTES list
    let baseIndex = Note.NOTES.indexOf(baseNote);

    // Apply the accidental shift and adjust for octave if necessary
    let shiftedIndex = (baseIndex + accidentalCount) % 12;
    let newOctave = this.octave;

    let enharmonicNote = Note.NOTES[shiftedIndex];

    if (letter) {
      // Find the letter and adjust accordingly
      let letterIndex = Note.NOTES.indexOf(letter);
      let diff = (shiftedIndex - letterIndex) % 12;
      if (diff > 6) {
        diff -= 12;
      } else if (diff < -6) {
        diff += 12;
      }

      // Adjust accidentals based on the difference
      if (diff > 0) {
        enharmonicNote = letter + "#".repeat(diff);
      } else if (diff < 0) {
        enharmonicNote = letter + "b".repeat(-diff);
      }
    } else {
      if (favor === "flat" && enharmonicNote.includes("#")) {
        // If flat is favored, prefer flat enharmonic over sharp
        enharmonicNote = Note.NOTES[(shiftedIndex + 1) % 12] + "b";
      }
      if (force) {
        if (favor === "sharp" && ["C", "F"].includes(enharmonicNote)) {
          enharmonicNote = Note.NOTES[(shiftedIndex - 1) % 12] + "#";  // C# and F# for diatonic
        } else if (favor === "flat" && ["B", "E"].includes(enharmonicNote)) {
          enharmonicNote = Note.NOTES[(shiftedIndex + 1) % 12] + "b";  // Bb and Eb for diatonic
        }
      }
    }

    if (enharmonicNote === "B#") {
      newOctave -= 1;
    } else if (enharmonicNote === "Cb") {
      newOctave += 1;
    }

    return new Note(enharmonicNote, newOctave);
  }

  _getMidiValue() {
    /**
     * Calculate the MIDI value of the note based on the enharmonic equivalent.
     * 
     * @return {number} MIDI value (integer) for the note.
     */
    let baseNote = this.letter;
    let accidentalCount = (this.accidental.match(/#/g) || []).length - (this.accidental.match(/b/g) || []).length;
    let baseIndex = Note.NOTES.indexOf(baseNote);

    // Apply the accidental shift
    let shiftedIndex = (baseIndex + accidentalCount);

    // The MIDI value of C4 is 60, so calculate based on that
    return 12 * (this.octave + 1) + shiftedIndex;
  }

  _getFrequency() {
    /**
     * Calculate the frequency of the note using the standard equal-tempered scale,
     * where A4 is 440 Hz.
     * 
     * @return {number} The frequency of the note in Hertz.
     */
    return 440 * Math.pow(2, (this.midi - 69) / 12);
  }

  toString() {
    /**
     * Return a string representation of the note (e.g., 'A4').
     */
    return `${this.letter}${this.accidental}${this.octave}`;
  }

  static strToNote(string) {
    /**
     * Convert a string representation of a note (e.g., 'A4') to a Note object.
     * 
     * @param {string} string - The note string to convert.
     * @return {Note} The corresponding Note object.
     */
    const match = string.match(/([A-Ga-g]+)([0-9]+)/);
    if (match) {
      return new Note(match[1], parseInt(match[2], 10));
    }
    return null;
  }

  static intToNote(num) {
    /**
     * Convert a MIDI integer value to a Note object.
     * 
     * @param {number} num - The MIDI value.
     * @return {Note} The corresponding Note object.
     */
    return new Note(Note.NOTES[num % 12], Math.floor(num / 12) - 1);
  }

  toSemitones() {
    const equivThis = this.enharmonicEquiv()
    return Note.NOTES.indexOf(equivThis.letter + equivThis.accidental) + this.octave * 12 + 12;
  }

  // Addition of a note and interval
  add(interval) {
    const letters = "CDEFGAB";
    const note = Note.intToNote(this.toSemitones() + interval.toSemitones());

    const selfIndex = letters.indexOf(this.letter);
    const newLetter = letters[(selfIndex + interval.number - 1) % 7];
    
    return note.enharmonicEquiv({letter: newLetter}); // Assuming enharmonic equivalence handled in intToNote
  }

  // Subtraction of one note from another (returns an Interval)
  subtract(other) {
    const letters = "CDEFGAB";

    // Calculate the diatonic interval
    const selfIndex = letters.indexOf(this.letter);
    const otherIndex = letters.indexOf(other.letter);
    let diatonicInterval = (selfIndex - otherIndex) % 7 + 1;

    // Chromatic interval (semitones difference)
    const chromaticDifference = this.toSemitones() - other.toSemitones();

    // Account for octave difference
    let octaveDifference = this.octave - other.octave;
    if (selfIndex < otherIndex) octaveDifference -= 1;
    diatonicInterval += octaveDifference * 7;

    // Calculate the quality of the interval
    const intervals = [0, 2, 4, 5, 7, 9, 11];
    const baseSemitones = intervals[(diatonicInterval - 1) % 7] + octaveDifference * 12;
    const quality = chromaticDifference - baseSemitones;

    return new Interval(diatonicInterval, quality);
  }
}
