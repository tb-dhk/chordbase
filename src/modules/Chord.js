import Note from './Note'
import Interval from './Interval'
import Scale from './Scale'

export default class Chord {
  static MAINS = {
    "dim": ["P1", "m3", "D5", "D7", "M9", "P11", "M13"],
    "min": ["P1", "m3", "P5", "m7", "M9", "P11", "M13"],
    "dom": ["P1", "M3", "P5", "m7", "M9", "P11", "M13"],
    "maj": ["P1", "M3", "P5", "M7", "M9", "P11", "M13"]
  };

  constructor(...intervals) {
    this.intervals = intervals.sort((a, b) => a.number - b.number || a.quality - b.quality);
  }

  notes(base = new Note("C", 4)) {
    let notes = [base];
    for (let interval of this.intervals) {
      notes.push(base.add(interval));
    }
    return notes;
  }

  quality() {
    const intervals = this.intervals.map(i => String(i));
    if (intervals.includes("m3")) {
      if (intervals.includes("D5") && intervals.includes("D7")) {
        return "dim";
      } else {
        return "min";
      }
    } else if (intervals.includes("M7")) {
      return "maj"; // default to maj for simplicity
    } else {
      return "dom";
    }
  }

  sus() {
    const intervals = this.intervals.map(i => String(i));
    if (!intervals.includes("m3") && !intervals.includes("M3") && intervals.includes("M2")) {
      return "sus2";
    } else if (intervals.includes("M4")) {
      return "sus4";
    }
    return "";
  }

  structure() {
    if (this.intervals.length === 1 && String(this.intervals[0]) === "P5") {
      return "power";
    }

    let notes = Math.max(...this.intervals.filter(i => i % 2).map(i => i.quality));
    switch (notes) {
      case 1: return "unison";
      case 3: return "third";
      case 5: return "triad";
      case 7: return "seventh";
      case 9: return "ninth";
      case 11: return "eleventh";
      case 13: return "thirteenth";
      default: return "";
    }
  }

  id(base = null) {
    let intervals = this.intervals.map(i => i.toString());
    let mainNumber = "1";
    let sus = this.sus();
    let additions = [];

    let quality = this.quality()

    // Find highest matching interval
    let found = false;
    for (let i = 6; i > 0; i--) {
      for (let interval of intervals) {
        const ls = Object.values(Chord.MAINS).map(m => m[i]).reverse();
        if (ls.includes(interval)) {
          mainNumber = interval.substring(1);
          found = true;
          break;
        }
      }
      if (found) break;
    }

    if (sus === "sus2" && intervals.includes("M4")) {
      additions.push(new Interval(4, 0));
    }

    const aug = intervals.includes("A5");

    const alterations = [];
    for (let interval of intervals) {
      const number = parseInt(interval.substring(1));
      const expectedInterval = Chord.MAINS[quality][Math.floor(number / 2)];
      if (number % 2 === 1 && interval !== expectedInterval) {
        alterations.push(new Interval(interval));
      } else if (number % 2 === 0 && sus.slice(3) !== String(number)) {
        additions.push(new Interval(interval));
      }
    }

    let alts = alterations.map(alt => (alt.quality > 0 ? "#" : alt.quality < 0 ? "b" : "") + alt.number);
    let adds = additions.map(add => (add.quality > 0 ? "#" : add.quality < 0 ? "b" : "") + add.number);

    quality = quality === "dom" || (quality === "maj" && parseInt(mainNumber) <= 5) ? "" : quality
    mainNumber = mainNumber === "5" || mainNumber === "1" ? "" : mainNumber.toString()
    return (base ? base.letter : "") + "^" + (aug ? "aug" : "") + sus + quality + mainNumber + alts.join("") + adds.join("");
  }

  inversions() {
    let newints = [this.intervals];
    const cycle = intervals => {
      let newset = [...intervals];
      let newOctave = Math.floor((newset[newset.length - 1].number - 1) / 7) + 1;
      newset.push(new Interval(7 * newOctave + 1, 0));
      newset = newset.slice(1).map(i => i - newset[0]);
      return newset;
    };

    for (let i = 0; i < this.intervals.length; i++) {
      newints.push(cycle(newints[newints.length - 1]));
    }

    return newints.slice(1).map(ints => new Chord(...ints));
  }

  static idToChord(chordid) {
    // Regular expressions for parsing
    const basePattern = /^[A-G][#b]*/; // Base note (e.g., C, Bb, F#)
    const augPattern = /aug/; // "aug" for augmented
    const susPattern = /(sus\d+)/; // Sus chords (e.g., sus4, sus2)
    const qualityPattern = /(\^min|\^maj|\^aug|\^dim|\^dom)/; // Quality (min, maj, etc.)
    const mainNumberPattern = /(\d+)/; // Main number (e.g., 7, 9, 13)
    const alterationPattern = /([b#♮]\d+)/g; // Alterations (e.g., #5, b9)
    const additionPattern = /add[b#]?\d+/g; // Additions (e.g., add9, add#11)

    // Parse base note
    const baseMatch = chordid.match(basePattern);
    const base = baseMatch ? baseMatch[0] : null;

    // Parse aug
    const augMatch = chordid.match(augPattern);
    const aug = augMatch ? augMatch[0] : null;

    // Parse sus
    const susMatch = chordid.match(susPattern);
    const sus = susMatch ? susMatch[0] : "";

    // Parse quality
    const qualityMatch = chordid.match(qualityPattern);
    const quality = qualityMatch ? qualityMatch[0].slice(1) : "dom";

    // Parse main number
    const mainNumberMatch = chordid.match(mainNumberPattern);
    const mainNumber = mainNumberMatch ? parseInt(mainNumberMatch[0]) : 5;

    // Parse alterations and additions
    const alterations = chordid.match(alterationPattern) || [];
    const additions = chordid.match(additionPattern) || [];

    // Convert to intervals
    let intervals = [];
    let existing5 = false;

    // Loop through MAINS based on the quality and main number
    for (let i = 0; i < Chord.MAINS[quality].length; i++) {
      const interval = Chord.MAINS[quality][i+1];
      if (i + 1 <= Math.floor(mainNumber / 2)) {
        if (aug && interval === "P5") {
          existing5 = true;
          intervals.push(Interval.strToInterval("A5"));
        } else {
          intervals.push(Interval.strToInterval(interval));
        }
      }
    }

    // Handle the augmentation if necessary
    if (aug && !existing5) {
      intervals.push(Interval.strToInterval("A5"));
    }

    // Handle sus intervals
    if (sus) {
      intervals.push(Interval.strToInterval("M" + sus.slice(3)));
    }

    // Handle additions
    additions.forEach(add => {
      const numSharps = (add.match(/#/g) || []).length;
      const numFlats = (add.match(/b/g) || []).length;
      const quality = numSharps - numFlats;
      const number = parseInt(add.replace(/\D/g, ""));
      intervals.push(new Interval(number, quality));
    });

    // Handle alterations
    alterations.forEach(alt => {
      if (!additions.includes("add" + alt)) {
        const numSharps = (alt.match(/#/g) || []).length;
        const numFlats = (alt.match(/b/g) || []).length;
        const quality = numSharps - numFlats;
        const number = parseInt(alt.replace(/\D/g, ""));
        intervals = intervals.filter(interval => interval.number !== number);
        intervals.push(new Interval(number, quality));
      }
    });

    // Return the reconstructed Chord object
    if (base) {
      return new ChordWithBase(new Note(base, 4), ...intervals);
    } else {
      return new Chord(...intervals);
    }
  }
}

class ChordWithBase extends Chord {
  constructor(base, ...intervals) {
    super(...intervals);
    this.base = base;
  }

  notes(base = this.base) {
    return super.notes(base);
  }

  id(base = this.base) {
    return super.id(base);
  }

  inversions() {
    const ls = super.inversions();
    for (let i = 0; i < this.intervals.length; i++) {
      ls[i] = new ChordWithBase(this.notes()[i], ...ls[i].intervals);
    }
    return ls;
  }

  transpositions() {
    return Note.NOTES.map(n => new ChordWithBase(new Note(n, 4), ...this.intervals));
  }

  subchords() {
    const dic = {};
    const notesToCompare = this.notes();
    for (let i = 0; i < notesToCompare.length; i++) {
      for (let j = i + 1; j < notesToCompare.length; j++) {
        const baseNote = notesToCompare[i];
        const notesInChord = notesToCompare.slice(i, j + 1);
        const intervals = notesInChord.map(note => note.subtract(baseNote));
        const chord = new ChordWithBase(baseNote, ...intervals.slice(1));
        const intervalBetweenFirstAndLast = intervals[intervals.length - 1].number;

        if (!dic[intervalBetweenFirstAndLast]) {
          dic[intervalBetweenFirstAndLast] = [];
        }
        dic[intervalBetweenFirstAndLast].push(chord);
      }
    }

    return dic;
  }

  extensions() {
    const chordQuality = this.quality();
    if (!(chordQuality in Chord.MAINS)) {
      return [];
    }

    const allIntervals = Chord.MAINS[chordQuality].slice(1);
    const existingIntervals = new Set(this.intervals.map(i => String(i)));
    let possibleChords = [this];

    for (let interval of allIntervals) {
      if (!existingIntervals.has(String(interval))) {
        const newIntervals = [...possibleChords[possibleChords.length - 1].intervals, Interval.strToInterval(interval)];
        possibleChords.push(new ChordWithBase(this.base, ...newIntervals));
      }
    }

    return possibleChords.slice(1);
  }

  simplifications() {
    let oddIntervals = this.intervals.filter(i => i.number % 2 === 1);
    let simplifications = [];
    let currentIntervals = [...this.intervals];

    while (currentIntervals.length > 1) {
      oddIntervals = currentIntervals.filter(i => i.number % 2 === 1);
      if (oddIntervals.length === 0) {
        break;
      }

      const highestOdd = Math.max(...oddIntervals.map(i => i.number));
      currentIntervals = currentIntervals.filter(i => i.number !== highestOdd);

      const simplifiedChord = new ChordWithBase(this.base, ...currentIntervals);
      simplifications.push(simplifiedChord);
    }

    return simplifications;
  }

  findMatchingScales() {
    const chordNotes = this.notes().map(n => n.toSemitones() % 12);
    const scales = {};

    for (let note of Note.NOTES) {
      for (let scale of Scale.SCALES) {
        const fullScale = Scale.generateScale(scale, new Note(note, 4));
        const scaleNotes = fullScale.notes().map(n => n.toSemitones() % 12);
        const count = chordNotes.filter(n => scaleNotes.includes(n)).length;
        const proportion = count / chordNotes.length;

        if (!scales[proportion]) {
          scales[proportion] = [];
        }
        scales[proportion].push(`${note} ${scale}`);
      }
    }

    return scales;
  }

  toString() {
    return `${this.base} ${this.intervals}`;
  }
}
