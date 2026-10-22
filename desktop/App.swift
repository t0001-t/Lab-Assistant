import Cocoa
import WebKit

final class AppDelegate: NSObject, NSApplicationDelegate, NSWindowDelegate, WKNavigationDelegate, WKUIDelegate, WKDownloadDelegate {
    var window: NSWindow!
    var webView: WKWebView!
    var backend: Process?
    var timer: Timer?
    var readyFile: URL!
    var startupTime = Date()
    var appURL: URL?
    var logFile: FileHandle?
    var quitting = false

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.regular)
        installMenus()
        let config = WKWebViewConfiguration()
        config.websiteDataStore = .default()
        webView = WKWebView(frame: .zero, configuration: config)
        webView.navigationDelegate = self
        webView.uiDelegate = self
        window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 1360, height: 900),
                          styleMask: [.titled, .closable, .miniaturizable, .resizable], backing: .buffered, defer: false)
        window.title = "Lab Assistant"
        window.minSize = NSSize(width: 980, height: 650)
        window.contentView = webView
        window.delegate = self
        window.center()
        window.setFrameAutosaveName("LabAssistantMainWindow")
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        webView.loadHTMLString("<html lang='de'><body style='font:18px system-ui;background:#f7f9fc;color:#2563a6;display:grid;place-content:center;height:90vh;text-align:center'><h1>Lab Assistant</h1><p>Dein Labor wird gestartet …</p></body></html>", baseURL: nil)
        startBackend()
    }

    func installMenus() {
        let menu = NSMenu()
        let appItem = NSMenuItem()
        let appMenu = NSMenu()
        appMenu.addItem(withTitle: "Über Lab Assistant", action: #selector(showAbout), keyEquivalent: "")
        appMenu.addItem(.separator())
        appMenu.addItem(withTitle: "Lab Assistant beenden", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        appItem.submenu = appMenu
        menu.addItem(appItem)
        let editItem = NSMenuItem()
        let edit = NSMenu(title: "Bearbeiten")
        edit.addItem(withTitle: "Widerrufen", action: Selector(("undo:")), keyEquivalent: "z")
        edit.addItem(withTitle: "Ausschneiden", action: #selector(NSText.cut(_:)), keyEquivalent: "x")
        edit.addItem(withTitle: "Kopieren", action: #selector(NSText.copy(_:)), keyEquivalent: "c")
        edit.addItem(withTitle: "Einfügen", action: #selector(NSText.paste(_:)), keyEquivalent: "v")
        edit.addItem(withTitle: "Alles auswählen", action: #selector(NSText.selectAll(_:)), keyEquivalent: "a")
        editItem.submenu = edit
        menu.addItem(editItem)
        let viewItem = NSMenuItem()
        let view = NSMenu(title: "Ansicht")
        view.addItem(withTitle: "Neu laden", action: #selector(reload), keyEquivalent: "r")
        view.addItem(withTitle: "Im Browser öffnen", action: #selector(openBrowser), keyEquivalent: "")
        viewItem.submenu = view
        menu.addItem(viewItem)
        let windowItem = NSMenuItem()
        let windowMenu = NSMenu(title: "Fenster")
        windowMenu.addItem(withTitle: "Minimieren", action: #selector(NSWindow.performMiniaturize(_:)), keyEquivalent: "m")
        windowItem.submenu = windowMenu
        menu.addItem(windowItem)
        NSApp.mainMenu = menu
        NSApp.windowsMenu = windowMenu
    }

    func startBackend() {
        do {
            let home = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0].appendingPathComponent("Lab Assistant PWA", isDirectory: true)
            try FileManager.default.createDirectory(at: home, withIntermediateDirectories: true)
            readyFile = home.appendingPathComponent("ready-\(ProcessInfo.processInfo.processIdentifier).json")
            let logURL = home.appendingPathComponent("app.log")
            FileManager.default.createFile(atPath: logURL.path, contents: nil)
            logFile = try FileHandle(forWritingTo: logURL)
            let process = Process()
            process.executableURL = Bundle.main.resourceURL!.appendingPathComponent("backend/LabAssistantServer")
            process.arguments = ["--app-home", home.path, "--ready-file", readyFile.path]
            process.standardOutput = logFile
            process.standardError = logFile
            var environment = ProcessInfo.processInfo.environment
            environment["PYTHONUNBUFFERED"] = "1"
            process.environment = environment
            backend = process
            try process.run()
            startupTime = Date()
            timer = Timer.scheduledTimer(withTimeInterval: 0.25, repeats: true) { [weak self] _ in self?.checkReady() }
        } catch { showFailure(error.localizedDescription) }
    }

    func checkReady() {
        if let data = try? Data(contentsOf: readyFile),
           let object = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
           let text = object["url"] as? String, let url = URL(string: text) {
            timer?.invalidate()
            appURL = url
            var components = URLComponents(url: url, resolvingAgainstBaseURL: false)!
            components.queryItems = [URLQueryItem(name: "desktopVersion", value: "1.0.3")]
            var request = URLRequest(url: components.url!)
            request.cachePolicy = .reloadIgnoringLocalCacheData
            webView.load(request)
        } else if backend?.isRunning == false || Date().timeIntervalSince(startupTime) > 90 {
            timer?.invalidate()
            showFailure("Der lokale Server konnte nicht gestartet werden. Details stehen in ~/Library/Application Support/Lab Assistant PWA/app.log.")
        }
    }

    func showFailure(_ message: String) {
        let alert = NSAlert()
        alert.messageText = "Lab Assistant konnte nicht starten"
        alert.informativeText = message
        alert.addButton(withTitle: "Beenden")
        alert.runModal()
        NSApp.terminate(nil)
    }

    @objc func showAbout() {
        NSApp.orderFrontStandardAboutPanel(options: [.applicationName: "Lab Assistant", .applicationVersion: "1.0.3", .version: "1"])
    }
    @objc func reload() { webView.reload() }
    @objc func openBrowser() { if let url = appURL { NSWorkspace.shared.open(url) } }
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }
    func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows flag: Bool) -> Bool {
        window.makeKeyAndOrderFront(nil)
        return true
    }
    func applicationWillTerminate(_ notification: Notification) {
        quitting = true
        timer?.invalidate()
        if let process = backend, process.isRunning {
            process.terminate()
            let deadline = Date().addingTimeInterval(10)
            while process.isRunning && Date() < deadline { Thread.sleep(forTimeInterval: 0.05) }
            if process.isRunning { kill(process.processIdentifier, SIGKILL) }
        }
        if let file = readyFile { try? FileManager.default.removeItem(at: file) }
        try? logFile?.close()
    }

    func webView(_ webView: WKWebView, decidePolicyFor action: WKNavigationAction, decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        if action.shouldPerformDownload { decisionHandler(.download); return }
        if let url = action.request.url, let host = url.host, host != "127.0.0.1" && host != "localhost" {
            NSWorkspace.shared.open(url)
            decisionHandler(.cancel)
        } else { decisionHandler(.allow) }
    }
    func webView(_ webView: WKWebView, decidePolicyFor response: WKNavigationResponse, decisionHandler: @escaping (WKNavigationResponsePolicy) -> Void) {
        decisionHandler(response.canShowMIMEType ? .allow : .download)
    }
    func webView(_ webView: WKWebView, navigationAction: WKNavigationAction, didBecome download: WKDownload) { download.delegate = self }
    func webView(_ webView: WKWebView, navigationResponse: WKNavigationResponse, didBecome download: WKDownload) { download.delegate = self }
    func download(_ download: WKDownload, decideDestinationUsing response: URLResponse, suggestedFilename: String, completionHandler: @escaping (URL?) -> Void) {
        let panel = NSSavePanel()
        panel.nameFieldStringValue = suggestedFilename
        panel.beginSheetModal(for: window) { result in completionHandler(result == .OK ? panel.url : nil) }
    }
    func webView(_ webView: WKWebView, runOpenPanelWith parameters: WKOpenPanelParameters, initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping ([URL]?) -> Void) {
        let panel = NSOpenPanel()
        panel.allowsMultipleSelection = parameters.allowsMultipleSelection
        panel.canChooseDirectories = parameters.allowsDirectories
        panel.canChooseFiles = true
        panel.beginSheetModal(for: window) { result in completionHandler(result == .OK ? panel.urls : nil) }
    }
    func webView(_ webView: WKWebView, runJavaScriptAlertPanelWithMessage message: String, initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping () -> Void) {
        let alert = NSAlert(); alert.messageText = message
        alert.beginSheetModal(for: window) { _ in completionHandler() }
    }
    func webView(_ webView: WKWebView, runJavaScriptConfirmPanelWithMessage message: String, initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping (Bool) -> Void) {
        let alert = NSAlert(); alert.messageText = message
        alert.addButton(withTitle: "OK"); alert.addButton(withTitle: "Abbrechen")
        alert.beginSheetModal(for: window) { result in completionHandler(result == .alertFirstButtonReturn) }
    }
}
let application = NSApplication.shared
let delegate = AppDelegate()
application.delegate = delegate
application.run()
