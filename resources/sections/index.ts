import { ISectionItem, ISectionFile, ISectionDefinition } from 'app/models/models/section';

import colorsJson from './colors.json';
import shapesJson from './shapes.json';
import bodyPartsJson from './body-parts.json';
import familyRelativesJson from './family-relatives.json';
import animalsBirdsJson from './animals-birds.json';
import fruitsVegetablesFlowersJson from './fruits-vegetables-flowers.json';
import foodDrinksJson from './food-drinks.json';
import gadgetsJson from './gadgets.json';
import vehiclesJson from './vehicles.json';
import musicalInstrumentsJson from './musical-instruments.json';
import homeHouseholdJson from './home-household.json';
import schoolClassroomJson from './school-classroom.json';
import professionsJson from './professions.json';
import placesJson from './places.json';
import directionsEarthJson from './directions-earth.json';
import timeCalendarJson from './time-calendar.json';
import weatherJson from './weather.json';
import emotionsJson from './emotions.json';
import dailyActivitiesJson from './daily-activities.json';
import festivalsCultureJson from './festivals-culture.json';

export const ColorsFile = colorsJson as ISectionFile;
export const ShapesFile = shapesJson as ISectionFile;
export const BodyPartsFile = bodyPartsJson as ISectionFile;
export const FamilyRelativesFile = familyRelativesJson as ISectionFile;
export const AnimalsBirdsFile = animalsBirdsJson as ISectionFile;
export const FruitsVegetablesFlowersFile = fruitsVegetablesFlowersJson as ISectionFile;
export const FoodDrinksFile = foodDrinksJson as ISectionFile;
export const GadgetsFile = gadgetsJson as ISectionFile;
export const VehiclesFile = vehiclesJson as ISectionFile;
export const MusicalInstrumentsFile = musicalInstrumentsJson as ISectionFile;
export const HomeHouseholdFile = homeHouseholdJson as ISectionFile;
export const SchoolClassroomFile = schoolClassroomJson as ISectionFile;
export const ProfessionsFile = professionsJson as ISectionFile;
export const PlacesFile = placesJson as ISectionFile;
export const DirectionsEarthFile = directionsEarthJson as ISectionFile;
export const TimeCalendarFile = timeCalendarJson as ISectionFile;
export const WeatherFile = weatherJson as ISectionFile;
export const EmotionsFile = emotionsJson as ISectionFile;
export const DailyActivitiesFile = dailyActivitiesJson as ISectionFile;
export const FestivalsCultureFile = festivalsCultureJson as ISectionFile;

export const ColorsData: ISectionItem[] = ColorsFile.items;
export const ShapesData: ISectionItem[] = ShapesFile.items;
export const BodyPartsData: ISectionItem[] = BodyPartsFile.items;
export const FamilyRelativesData: ISectionItem[] = FamilyRelativesFile.items;
export const AnimalsBirdsData: ISectionItem[] = AnimalsBirdsFile.items;
export const FruitsVegetablesFlowersData: ISectionItem[] = FruitsVegetablesFlowersFile.items;
export const FoodDrinksData: ISectionItem[] = FoodDrinksFile.items;
export const GadgetsData: ISectionItem[] = GadgetsFile.items;
export const VehiclesData: ISectionItem[] = VehiclesFile.items;
export const MusicalInstrumentsData: ISectionItem[] = MusicalInstrumentsFile.items;
export const HomeHouseholdData: ISectionItem[] = HomeHouseholdFile.items;
export const SchoolClassroomData: ISectionItem[] = SchoolClassroomFile.items;
export const ProfessionsData: ISectionItem[] = ProfessionsFile.items;
export const PlacesData: ISectionItem[] = PlacesFile.items;
export const DirectionsEarthData: ISectionItem[] = DirectionsEarthFile.items;
export const TimeCalendarData: ISectionItem[] = TimeCalendarFile.items;
export const WeatherData: ISectionItem[] = WeatherFile.items;
export const EmotionsData: ISectionItem[] = EmotionsFile.items;
export const DailyActivitiesData: ISectionItem[] = DailyActivitiesFile.items;
export const FestivalsCultureData: ISectionItem[] = FestivalsCultureFile.items;

export const ALL_SECTIONS: ISectionDefinition[] = [
  { id: 'colors', sectionNumber: 3, title_en: 'Colors', title_gu: 'રંગો', icon: 'palette', totalItems: ColorsFile.totalItems, items: ColorsData },
  { id: 'shapes', sectionNumber: 4, title_en: 'Shapes', title_gu: 'આકારો', icon: 'shapes', totalItems: ShapesFile.totalItems, items: ShapesData },
  { id: 'body_parts', sectionNumber: 5, title_en: 'Body Parts', title_gu: 'શરીરના અંગો', icon: 'accessibility', totalItems: BodyPartsFile.totalItems, items: BodyPartsData },
  { id: 'family_relatives', sectionNumber: 6, title_en: 'Family & Relatives', title_gu: 'કુટુંબ અને સગાં-સંબંધીઓ', icon: 'people', totalItems: FamilyRelativesFile.totalItems, items: FamilyRelativesData },
  { id: 'animals_birds', sectionNumber: 7, title_en: 'Animals & Birds', title_gu: 'પ્રાણીઓ અને પક્ષીઓ', icon: 'pets', totalItems: AnimalsBirdsFile.totalItems, items: AnimalsBirdsData },
  { id: 'fruits_vegetables_flowers', sectionNumber: 8, title_en: 'Fruits, Veg & Flowers', title_gu: 'ફળો, શાકભાજી અને ફૂલો', icon: 'nutrition', totalItems: FruitsVegetablesFlowersFile.totalItems, items: FruitsVegetablesFlowersData },
  { id: 'food_drinks', sectionNumber: 9, title_en: 'Food & Drinks', title_gu: 'ખોરાક અને પીણાં', icon: 'restaurant', totalItems: FoodDrinksFile.totalItems, items: FoodDrinksData },
  { id: 'gadgets', sectionNumber: 10, title_en: 'Gadgets & Technology', title_gu: 'ગેજેટ્સ અને ટેકનોલોજી', icon: 'devices', totalItems: GadgetsFile.totalItems, items: GadgetsData },
  { id: 'vehicles', sectionNumber: 11, title_en: 'Vehicles', title_gu: 'વાહનો', icon: 'directions-car', totalItems: VehiclesFile.totalItems, items: VehiclesData },
  { id: 'musical_instruments', sectionNumber: 12, title_en: 'Musical Instruments', title_gu: 'સંગીતના સાધનો', icon: 'music-note', totalItems: MusicalInstrumentsFile.totalItems, items: MusicalInstrumentsData },
  { id: 'home_household', sectionNumber: 13, title_en: 'Home & Household', title_gu: 'ઘર અને ઘરવખરી', icon: 'home', totalItems: HomeHouseholdFile.totalItems, items: HomeHouseholdData },
  { id: 'school_classroom', sectionNumber: 14, title_en: 'School & Classroom', title_gu: 'શાળા અને વર્ગખંડ', icon: 'school', totalItems: SchoolClassroomFile.totalItems, items: SchoolClassroomData },
  { id: 'professions', sectionNumber: 15, title_en: 'Professions', title_gu: 'વ્યવસાયો અને કારીગરો', icon: 'work', totalItems: ProfessionsFile.totalItems, items: ProfessionsData },
  { id: 'places', sectionNumber: 16, title_en: 'Places', title_gu: 'સ્થળો અને જાહેર જગ્યાઓ', icon: 'place', totalItems: PlacesFile.totalItems, items: PlacesData },
  { id: 'directions_earth', sectionNumber: 17, title_en: 'Directions & Earth', title_gu: 'દિશાઓ અને પૃથ્વી', icon: 'explore', totalItems: DirectionsEarthFile.totalItems, items: DirectionsEarthData },
  { id: 'time_calendar', sectionNumber: 18, title_en: 'Time & Calendar', title_gu: 'સમય અને કેલેન્ડર', icon: 'calendar-today', totalItems: TimeCalendarFile.totalItems, items: TimeCalendarData },
  { id: 'weather', sectionNumber: 19, title_en: 'Weather', title_gu: 'હવામાન', icon: 'wb-sunny', totalItems: WeatherFile.totalItems, items: WeatherData },
  { id: 'emotions', sectionNumber: 20, title_en: 'Emotions', title_gu: 'લાગણીઓ અને ભાવો', icon: 'sentiment-satisfied', totalItems: EmotionsFile.totalItems, items: EmotionsData },
  { id: 'daily_activities', sectionNumber: 21, title_en: 'Daily Activities', title_gu: 'દિનચર્યા અને ક્રિયાઓ', icon: 'schedule', totalItems: DailyActivitiesFile.totalItems, items: DailyActivitiesData },
  { id: 'festivals_culture', sectionNumber: 22, title_en: 'Festivals & Culture', title_gu: 'તહેવારો અને સંસ્કૃતિ', icon: 'celebration', totalItems: FestivalsCultureFile.totalItems, items: FestivalsCultureData },
];

export const SECTIONS_MAP: Record<string, ISectionDefinition> = ALL_SECTIONS.reduce((acc, section) => {
  acc[section.id] = section;
  return acc;
}, {} as Record<string, ISectionDefinition>);

export const getSectionById = (id: string): ISectionDefinition | undefined => {
  return SECTIONS_MAP[id];
};

export const getSectionByNumber = (sectionNumber: number): ISectionDefinition | undefined => {
  return ALL_SECTIONS.find(s => s.sectionNumber === sectionNumber);
};
