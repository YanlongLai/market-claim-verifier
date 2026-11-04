// Host-only local OCR of the actual review PNGs. No network or model provider.
import Foundation
import AppKit
import Vision
var rows:[[String:Any]]=[]
for path in CommandLine.arguments.dropFirst() {
    let url=URL(fileURLWithPath:path)
    let request=VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.recognitionLanguages=["en-US","zh-Hans","zh-Hant"]
    request.usesLanguageCorrection=false
    do {
        try VNImageRequestHandler(url:url).perform([request])
        let strings=(request.results ?? []).compactMap { $0.topCandidates(1).first?.string }
        rows.append(["file":path,"text":strings])
    } catch {
        FileHandle.standardError.write(Data("OCR failed for a review frame.\n".utf8))
        exit(1)
    }
}
let output=try JSONSerialization.data(withJSONObject:rows,options:[.prettyPrinted,.sortedKeys])
FileHandle.standardOutput.write(output)
