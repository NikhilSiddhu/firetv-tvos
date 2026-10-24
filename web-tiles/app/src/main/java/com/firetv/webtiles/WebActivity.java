package com.firetv.webtiles;

import android.app.Activity;
import android.graphics.Color;
import android.os.Bundle;
import android.view.KeyEvent;
import android.view.View;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.ProgressBar;
import android.widget.TextView;

/** Full-screen browser for one shortcut. Back leaves; the D-pad scrolls as usual. */
public class WebActivity extends Activity {

    public static final String EXTRA_URL = "url";
    public static final String EXTRA_NAME = "name";

    private WebView web;
    private ProgressBar bar;
    private TextView title;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_web);

        web = findViewById(R.id.web);
        bar = findViewById(R.id.bar);
        title = findViewById(R.id.web_title);

        String url = getIntent().getStringExtra(EXTRA_URL);
        String name = getIntent().getStringExtra(EXTRA_NAME);
        if (name != null) title.setText(name);

        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setLoadWithOverviewMode(true);
        s.setUseWideViewPort(true);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setUserAgentString(s.getUserAgentString().replace("; wv", ""));

        web.setBackgroundColor(Color.BLACK);
        web.setWebViewClient(new WebViewClient());
        web.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onProgressChanged(WebView view, int newProgress) {
                bar.setProgress(newProgress);
                bar.setVisibility(newProgress >= 100 ? View.GONE : View.VISIBLE);
            }

            @Override
            public void onReceivedTitle(WebView view, String t) {
                if (t != null && !t.isEmpty()) title.setText(t);
            }
        });

        web.loadUrl(TileStore.normaliseUrl(url));
    }

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_BACK && web.canGoBack()) {
            web.goBack();
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }

    @Override
    protected void onDestroy() {
        if (web != null) {
            web.stopLoading();
            web.destroy();
            web = null;
        }
        super.onDestroy();
    }
}
