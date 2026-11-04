import Foundation
import CoreText
let regular = CTFontCreateWithName("ArialMT" as CFString, 96, nil)
let bold = CTFontCreateWithName("Arial-BoldMT" as CFString, 96, nil)
func metrics(_ text: String, _ font: CTFont) -> [String: Any] {
    let attributed = NSAttributedString(string: text, attributes: [NSAttributedString.Key(rawValue: kCTFontAttributeName as String): font])
    let line = CTLineCreateWithAttributedString(attributed)
    let bounds = CTLineGetBoundsWithOptions(line, [.useGlyphPathBounds])
    return ["text": text, "advance": CTLineGetTypographicBounds(line, nil, nil, nil), "glyph_bottom": bounds.minY, "glyph_top": bounds.maxY, "glyph_center": bounds.midY, "x_height_center": CTFontGetXHeight(font) / 2]
}
let credit = CTFontCreateWithName("ArialMT" as CFString, 56, nil)
let report: [String: Any] = ["method": "CoreText font geometry; source layout only, not a Chromium or encoded-frame audit", "operators": [metrics("−", regular), metrics("=", regular)], "numbers": ["$416.2B", "$313.7B", "$102.5B"].map { metrics($0, bold) }, "credit": metrics("Built with Meta Muse Spark · Baseten · Fireworks · Meta Model API", credit), "credit_available_width": 1760, "draft_card": ["height": 232.0, "title_line": 56.0 * 1.15, "number_line": 96.0 * 1.08, "gap": 10.0, "top_and_bottom_space": (232.0 - 56.0 * 1.15 - 96.0 * 1.08 - 10.0) / 2]]
let data = try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys])
print(String(data: data, encoding: .utf8)!)
