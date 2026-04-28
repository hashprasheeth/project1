export type RecyclingBin =
  | 'E-Waste'
  | 'Battery'
  | 'Hazardous Facility'
  | 'Metal Recovery'
  | 'Appliance'
  | 'Data Destruction'
  | 'Medical Waste'
  | 'General Recycling'
  | 'Glass'
  | 'Plastic Sorting';

export interface EwasteClass {
  readonly id: number;
  readonly name: string;
  readonly hazardous: boolean;
  readonly recyclingBin: RecyclingBin;
  readonly description: string;
}

export const EWASTE_CLASSES: readonly EwasteClass[] = [
  { id: 0, name: 'Electronic-Waste', hazardous: true, recyclingBin: 'E-Waste', description: 'General electronic waste requiring specialized processing' },
  { id: 1, name: 'Air-Conditioner', hazardous: true, recyclingBin: 'Hazardous Facility', description: 'Contains refrigerants and compressor oils requiring safe extraction' },
  { id: 2, name: 'Bar-Phone', hazardous: false, recyclingBin: 'E-Waste', description: 'Basic mobile phone with minimal hazardous components' },
  { id: 3, name: 'Battery', hazardous: true, recyclingBin: 'Battery', description: 'Chemical energy storage requiring specialized recycling to prevent leaks' },
  { id: 4, name: 'Blood-Pressure-Monitor', hazardous: false, recyclingBin: 'Medical Waste', description: 'Medical monitoring device with electronic components' },
  { id: 5, name: 'Boiler', hazardous: true, recyclingBin: 'Hazardous Facility', description: 'Large heating appliance with pressurized components' },
  { id: 6, name: 'CRT-Monitor', hazardous: true, recyclingBin: 'Hazardous Facility', description: 'Contains lead, phosphors and high-voltage capacitors' },
  { id: 7, name: 'CRT-TV', hazardous: true, recyclingBin: 'Hazardous Facility', description: 'Cathode ray tube television with lead glass and toxic phosphors' },
  { id: 8, name: 'Calculator', hazardous: false, recyclingBin: 'E-Waste', description: 'Small electronic computing device with minimal hazardous materials' },
  { id: 9, name: 'Camera', hazardous: false, recyclingBin: 'E-Waste', description: 'Digital or analog imaging device with recoverable optics' },
  { id: 10, name: 'Ceiling-Fan', hazardous: false, recyclingBin: 'Appliance', description: 'Electric motor appliance with metal and plastic components' },
  { id: 11, name: 'Christmas-Lights', hazardous: false, recyclingBin: 'E-Waste', description: 'Decorative LED or incandescent string lights' },
  { id: 12, name: 'Clothes-Iron', hazardous: false, recyclingBin: 'Appliance', description: 'Heating appliance with metal soleplate and thermostat' },
  { id: 13, name: 'Coffee-Machine', hazardous: false, recyclingBin: 'Appliance', description: 'Kitchen appliance with heating elements and electronics' },
  { id: 14, name: 'Compact-Fluorescent-Lamps', hazardous: true, recyclingBin: 'Hazardous Facility', description: 'Contains mercury vapor requiring careful handling' },
  { id: 15, name: 'Computer-Keyboard', hazardous: false, recyclingBin: 'E-Waste', description: 'Input peripheral with plastic casing and circuit board' },
  { id: 16, name: 'Computer-Mouse', hazardous: false, recyclingBin: 'E-Waste', description: 'Input peripheral with small PCB and optical sensors' },
  { id: 17, name: 'Cooled-Dispenser', hazardous: true, recyclingBin: 'Hazardous Facility', description: 'Water dispenser with refrigerant cooling system' },
  { id: 18, name: 'Cooling-Display', hazardous: true, recyclingBin: 'Hazardous Facility', description: 'Commercial refrigerated display with refrigerant gases' },
  { id: 19, name: 'Dehumidifier', hazardous: true, recyclingBin: 'Hazardous Facility', description: 'Contains refrigerant and compressor requiring safe disposal' },
  { id: 20, name: 'Desktop-PC', hazardous: true, recyclingBin: 'Data Destruction', description: 'Computer system with data storage and multiple recoverable components' },
  { id: 21, name: 'Digital-Oscilloscope', hazardous: false, recyclingBin: 'E-Waste', description: 'Electronic test instrument with display and circuit boards' },
  { id: 22, name: 'Dishwasher', hazardous: false, recyclingBin: 'Appliance', description: 'Large kitchen appliance with motor and electronic controls' },
  { id: 23, name: 'Drone', hazardous: true, recyclingBin: 'Battery', description: 'UAV with lithium polymer batteries requiring careful handling' },
  { id: 24, name: 'Electric-Bicycle', hazardous: true, recyclingBin: 'Battery', description: 'Vehicle with large lithium battery pack and electric motor' },
  { id: 25, name: 'Electric-Guitar', hazardous: false, recyclingBin: 'E-Waste', description: 'Musical instrument with pickups and electronic components' },
  { id: 26, name: 'Electrocardiograph-Machine', hazardous: false, recyclingBin: 'Medical Waste', description: 'Medical diagnostic device requiring specialized disposal' },
  { id: 27, name: 'Electronic-Keyboard', hazardous: false, recyclingBin: 'E-Waste', description: 'Musical keyboard instrument with electronic sound generation' },
  { id: 28, name: 'Exhaust-Fan', hazardous: false, recyclingBin: 'Appliance', description: 'Ventilation device with electric motor' },
  { id: 29, name: 'Flashlight', hazardous: true, recyclingBin: 'Battery', description: 'Portable light source often containing batteries' },
  { id: 30, name: 'Flat-Panel-Monitor', hazardous: true, recyclingBin: 'E-Waste', description: 'LCD/LED display with backlight mercury lamps in older models' },
  { id: 31, name: 'Flat-Panel-TV', hazardous: true, recyclingBin: 'E-Waste', description: 'Large display with complex electronics and potential mercury backlights' },
  { id: 32, name: 'Floor-Fan', hazardous: false, recyclingBin: 'Appliance', description: 'Standing fan with electric motor and plastic blades' },
  { id: 33, name: 'Freezer', hazardous: true, recyclingBin: 'Hazardous Facility', description: 'Contains refrigerant gases and insulation foam with blowing agents' },
  { id: 34, name: 'Glucose-Meter', hazardous: false, recyclingBin: 'Medical Waste', description: 'Small medical device for blood sugar monitoring' },
  { id: 35, name: 'HDD', hazardous: true, recyclingBin: 'Data Destruction', description: 'Hard disk drive containing sensitive data and rare earth magnets' },
  { id: 36, name: 'Hair-Dryer', hazardous: false, recyclingBin: 'Appliance', description: 'Personal care appliance with heating element and motor' },
  { id: 37, name: 'Headphone', hazardous: false, recyclingBin: 'E-Waste', description: 'Audio device with small magnets and wiring' },
  { id: 38, name: 'LED-Bulb', hazardous: false, recyclingBin: 'General Recycling', description: 'Energy-efficient light source with electronic driver circuit' },
  { id: 39, name: 'Laptop', hazardous: true, recyclingBin: 'Data Destruction', description: 'Portable computer with battery, storage and display requiring careful processing' },
  { id: 40, name: 'Microwave', hazardous: true, recyclingBin: 'Hazardous Facility', description: 'Contains magnetron and high-voltage capacitor' },
  { id: 41, name: 'Music-Player', hazardous: false, recyclingBin: 'E-Waste', description: 'Portable audio device with small battery and storage' },
  { id: 42, name: 'Neon-Sign', hazardous: true, recyclingBin: 'Hazardous Facility', description: 'Contains inert gases and mercury, plus high-voltage transformer' },
  { id: 43, name: 'Network-Switch', hazardous: false, recyclingBin: 'E-Waste', description: 'Networking equipment with circuit boards and metal casing' },
  { id: 44, name: 'Non-Cooled-Dispenser', hazardous: false, recyclingBin: 'Appliance', description: 'Water dispenser without refrigerant system' },
  { id: 45, name: 'Oven', hazardous: false, recyclingBin: 'Appliance', description: 'Large cooking appliance with heating elements and controls' },
  { id: 46, name: 'PCB', hazardous: true, recyclingBin: 'Hazardous Facility', description: 'Printed circuit board containing lead solder, heavy metals and flame retardants' },
  { id: 47, name: 'Patient-Monitoring-System', hazardous: false, recyclingBin: 'Medical Waste', description: 'Complex medical device requiring specialized disposal' },
  { id: 48, name: 'Photovoltaic-Panel', hazardous: true, recyclingBin: 'Hazardous Facility', description: 'Solar panel containing cadmium, silicon and lead solder' },
  { id: 49, name: 'PlayStation-5', hazardous: false, recyclingBin: 'E-Waste', description: 'Gaming console with complex electronics and storage' },
  { id: 50, name: 'Power-Adapter', hazardous: false, recyclingBin: 'E-Waste', description: 'AC/DC power converter with transformer and capacitors' },
  { id: 51, name: 'Printer', hazardous: true, recyclingBin: 'E-Waste', description: 'Output device with toner/ink cartridges and electronic components' },
  { id: 52, name: 'Projector', hazardous: true, recyclingBin: 'E-Waste', description: 'Display device with mercury-containing lamp and optics' },
  { id: 53, name: 'Pulse-Oximeter', hazardous: false, recyclingBin: 'Medical Waste', description: 'Small medical sensor device' },
  { id: 54, name: 'Range-Hood', hazardous: false, recyclingBin: 'Appliance', description: 'Kitchen ventilation appliance with motor and filters' },
  { id: 55, name: 'Refrigerator', hazardous: true, recyclingBin: 'Hazardous Facility', description: 'Contains refrigerant gases, compressor oil and insulation foam' },
  { id: 56, name: 'Rotary-Mower', hazardous: true, recyclingBin: 'Battery', description: 'Garden equipment with battery or fuel engine' },
  { id: 57, name: 'Router', hazardous: false, recyclingBin: 'E-Waste', description: 'Network device with circuit board and antenna' },
  { id: 58, name: 'SSD', hazardous: true, recyclingBin: 'Data Destruction', description: 'Solid state drive containing sensitive data and flash memory' },
  { id: 59, name: 'Server', hazardous: true, recyclingBin: 'Data Destruction', description: 'Enterprise computing equipment with multiple drives and data' },
  { id: 60, name: 'Smart-Watch', hazardous: true, recyclingBin: 'Battery', description: 'Wearable device with small lithium battery and sensors' },
  { id: 61, name: 'Smartphone', hazardous: true, recyclingBin: 'Battery', description: 'Mobile device with lithium battery, rare earth elements and data' },
  { id: 62, name: 'Smoke-Detector', hazardous: true, recyclingBin: 'Hazardous Facility', description: 'May contain radioactive americium-241 isotope' },
  { id: 63, name: 'Soldering-Iron', hazardous: true, recyclingBin: 'Hazardous Facility', description: 'Tool with lead-contaminated tip requiring proper disposal' },
  { id: 64, name: 'Speaker', hazardous: false, recyclingBin: 'E-Waste', description: 'Audio device with magnets, cones and amplifier electronics' },
  { id: 65, name: 'Stove', hazardous: false, recyclingBin: 'Appliance', description: 'Cooking appliance with burners and electronic ignition' },
  { id: 66, name: 'Straight-Tube-Fluorescent-Lamp', hazardous: true, recyclingBin: 'Hazardous Facility', description: 'Contains mercury vapor requiring specialized recycling' },
  { id: 67, name: 'Street-Lamp', hazardous: true, recyclingBin: 'Hazardous Facility', description: 'Outdoor lighting with high-pressure discharge lamp or LED' },
  { id: 68, name: 'TV-Remote-Control', hazardous: false, recyclingBin: 'E-Waste', description: 'Small infrared device with minimal electronics and battery' },
  { id: 69, name: 'Table-Lamp', hazardous: false, recyclingBin: 'General Recycling', description: 'Desk lamp with basic electrical components' },
  { id: 70, name: 'Tablet', hazardous: true, recyclingBin: 'Data Destruction', description: 'Portable device with lithium battery, display and data storage' },
  { id: 71, name: 'Telephone-Set', hazardous: false, recyclingBin: 'E-Waste', description: 'Landline phone with basic circuit board and speaker' },
  { id: 72, name: 'Toaster', hazardous: false, recyclingBin: 'Appliance', description: 'Small kitchen appliance with heating elements' },
  { id: 73, name: 'Tumble-Dryer', hazardous: false, recyclingBin: 'Appliance', description: 'Large laundry appliance with motor and heating system' },
  { id: 74, name: 'USB-Flash-Drive', hazardous: false, recyclingBin: 'Data Destruction', description: 'Portable data storage device with flash memory' },
  { id: 75, name: 'Vacuum-Cleaner', hazardous: false, recyclingBin: 'Appliance', description: 'Cleaning appliance with motor, filters and electronic controls' },
  { id: 76, name: 'Washing-Machine', hazardous: false, recyclingBin: 'Appliance', description: 'Large laundry appliance with motor and electronic controls' },
  { id: 77, name: 'Xbox-Series-X', hazardous: false, recyclingBin: 'E-Waste', description: 'Gaming console with complex electronics and storage' },
] as const;

export const RECYCLING_BINS: readonly RecyclingBin[] = [
  'E-Waste',
  'Battery',
  'Hazardous Facility',
  'Metal Recovery',
  'Appliance',
  'Data Destruction',
  'Medical Waste',
  'General Recycling',
  'Glass',
  'Plastic Sorting',
] as const;

