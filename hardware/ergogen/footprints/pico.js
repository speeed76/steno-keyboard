// Raspberry Pi Pico / Pico 2 (and pin-compatible 40-pin modules), through-hole.
// Mounted component side up, USB connector pointing toward -y (top of the board).
// Pins 1-20 run down the left edge, 21-40 up the right edge, 2.54 mm pitch,
// rows 17.78 mm apart (Raspberry Pi Pico datasheet, mechanical drawing).
const PINS = [
  'GP0', 'GP1', 'GND', 'GP2', 'GP3', 'GP4', 'GP5', 'GND', 'GP6', 'GP7',
  'GP8', 'GP9', 'GND', 'GP10', 'GP11', 'GP12', 'GP13', 'GND', 'GP14', 'GP15',
  'GP16', 'GP17', 'GND', 'GP18', 'GP19', 'GP20', 'GP21', 'GND', 'GP22', 'RUN',
  'GP26', 'GP27', 'GND', 'GP28', 'ADC_VREF', '3V3', '3V3_EN', 'GND', 'VSYS', 'VBUS',
]

const params = { designator: 'MCU' }
for (const name of new Set(PINS)) {
  params[name] = { type: 'net', value: name }
}

module.exports = {
  params,
  body: p => {
    const pads = PINS.map((name, i) => {
      const n = i + 1
      const left = n <= 20
      const x = left ? -8.89 : 8.89
      const y = left ? -24.13 + (n - 1) * 2.54 : 24.13 - (n - 21) * 2.54
      const shape = n === 1 ? 'rect' : 'circle'
      const lx = left ? -5.6 : 5.6
      return `
        (pad ${n} thru_hole ${shape} (at ${x} ${y} ${p.r}) (size 1.7 1.7) (drill 1.02) (layers *.Cu *.Mask) ${p[name]})
        (fp_text user "${name}" (at ${lx} ${y} ${p.r}) (layer F.SilkS) (effects (font (size 0.7 0.7) (thickness 0.12))))`
    }).join('')
    return `
      (module RPi_Pico (layer F.Cu) (tedit 0)
        ${p.at}
        (fp_text reference "${p.ref}" (at 0 0 ${p.r}) (layer F.SilkS) ${p.ref_hide} (effects (font (size 1 1) (thickness 0.15))))
        (fp_text value "RPi Pico" (at 0 2 ${p.r}) (layer F.Fab) (effects (font (size 1 1) (thickness 0.15))))
        (fp_line (start -10.5 -25.5) (end 10.5 -25.5) (layer F.SilkS) (width 0.15))
        (fp_line (start 10.5 -25.5) (end 10.5 25.5) (layer F.SilkS) (width 0.15))
        (fp_line (start 10.5 25.5) (end -10.5 25.5) (layer F.SilkS) (width 0.15))
        (fp_line (start -10.5 25.5) (end -10.5 -25.5) (layer F.SilkS) (width 0.15))
        (fp_line (start -4 -25.5) (end -4 -26.8) (layer Dwgs.User) (width 0.15))
        (fp_line (start -4 -26.8) (end 4 -26.8) (layer Dwgs.User) (width 0.15))
        (fp_line (start 4 -26.8) (end 4 -25.5) (layer Dwgs.User) (width 0.15))
        (fp_text user "USB" (at 0 -23.5 ${p.r}) (layer F.SilkS) (effects (font (size 1 1) (thickness 0.15))))
        ${pads}
      )`
  }
}
