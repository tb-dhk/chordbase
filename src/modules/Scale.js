import Interval from './Interval'

export default class Scale {
  constructor(base, ...intervals) {
    this.base = base ? base : new Note("C", 4); // default base is C4
    this.intervals = intervals.sort((a, b) => a.number - b.number || a.quality - b.quality);
  }

  static SCALES = [
    "major",
    "natural minor", "harmonic minor", "melodic minor",
    "major pentatonic scale", "minor pentatonic scale",
    "blues scale"
  ];

  notes() {
    let notes = [this.base];
    for (let interval of this.intervals) {
      notes.push(this.base.add(interval));
    }
    return notes;
  }

  static generateScale(name, base = new Note("C", 4)) {
    const scale = new Scale(
      base,
      ...[...Array(6).keys()].map(i => new Interval(i+2, 0))
    );

    switch (name) {
      case "major":
        break;
      case "natural minor":
        [1, 4, 5].forEach(i => {
          scale.intervals[i].quality = -1;
        });
        break;
      case "harmonic minor":
        [1, 4].forEach(i => {
          scale.intervals[i].quality = -1;
        });
        break;
      case "melodic minor":
        scale.intervals[1].quality = -1;
        break;
      case "major pentatonic scale":
        scale.intervals = scale.intervals.filter((_, i) => ![2, 5].includes(i));
        break;
      case "minor pentatonic scale":
        [1, 5].forEach(i => {
          scale.intervals[i].quality = -1;
        });
        scale.intervals = scale.intervals.filter((_, i) => ![0, 4].includes(i));
        break;
      case "blues scale":
        [1, 5].forEach(i => {
          scale.intervals[i].quality = -1;
        });
        scale.intervals = scale.intervals.filter((_, i) => ![0, 4].includes(i));
        scale.intervals.push(new Interval(4, 1));
        scale.intervals.sort((a, b) => a.number - b.number || a.quality - b.quality);
        break;
      default:
        return new Scale(base);
    }

    return scale;
  }
}

class Note {
  constructor(name, octave) {
    this.name = name;
    this.octave = octave;
  }

  add(interval) {
    // Implement the logic to add the interval to the note and return a new note.
    // This is a placeholder implementation.
    return new Note(this.name, this.octave);
  }
}
