import { ALL_SECTIONS, SECTIONS_MAP, getSectionById, getSectionByNumber } from './index';

describe('Sections Data Integrity Tests', () => {
  it('should have exactly 20 distinct integration sections', () => {
    expect(ALL_SECTIONS.length).toBe(20);
  });

  it('each section should have valid metadata and non-empty items', () => {
    ALL_SECTIONS.forEach((section) => {
      expect(section.id).toBeDefined();
      expect(typeof section.id).toBe('string');
      expect(section.title_en).toBeDefined();
      expect(section.title_gu).toBeDefined();
      expect(section.sectionNumber).toBeGreaterThanOrEqual(3);
      expect(section.sectionNumber).toBeLessThanOrEqual(22);
      expect(section.items.length).toBeGreaterThan(0);
      expect(section.items.length).toBeLessThanOrEqual(50);
      expect(section.totalItems).toBe(section.items.length);

      // Verify each item structure
      section.items.forEach((item, index) => {
        expect(item.id).toBe(index + 1);
        expect(item.en).toBeDefined();
        expect(item.en.trim().length).toBeGreaterThan(0);
        expect(item.gu).toBeDefined();
        expect(item.gu.trim().length).toBeGreaterThan(0);
        expect(item.transliteration).toBeDefined();
      });
    });
  });

  it('should retrieve sections by id and section number correctly', () => {
    const colors = getSectionById('colors');
    expect(colors).toBeDefined();
    expect(colors?.title_en).toBe('Colors');
    expect(colors?.title_gu).toBe('રંગો');

    const shapes = getSectionByNumber(4);
    expect(shapes).toBeDefined();
    expect(shapes?.id).toBe('shapes');
    expect(shapes?.title_en).toBe('Shapes');
  });

  it('SECTIONS_MAP should index all 20 sections properly', () => {
    expect(Object.keys(SECTIONS_MAP).length).toBe(20);
  });
});
