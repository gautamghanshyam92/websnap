function printUrls() {
    console.log("hello....");
    function logTabs(tabs) {
        for (let tab of tabs) {
            // tab.url requires the `tabs` permission
            console.log(tab.url);
        }
    }
      
    function onError(error) {
        console.log(`Error(: ${error}) while getting list of all tabs.`);
    }
      
    var alltabs = browser.tabs.query({currentWindow: true});
    alltabs.then(logTabs, onError);
}
browser.browserAction.onClicked.addListener(printUrls);