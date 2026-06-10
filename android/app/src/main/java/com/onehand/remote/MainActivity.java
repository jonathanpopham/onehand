package com.onehand.remote;

import android.Manifest;
import android.annotation.SuppressLint;
import android.content.SharedPreferences;
import android.net.http.SslError;
import android.os.Bundle;
import android.view.View;
import android.webkit.PermissionRequest;
import android.webkit.SslErrorHandler;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;

/**
 * onehand Android client.
 *
 * A thin wrapper around the onehand web UI:
 *  - pairing screen: enter the Mac's address (or full URL) once, saved forever
 *  - accepts the Mac's self-signed certificate (LAN pairing model)
 *  - auto-grants the page microphone access so dictation works natively
 */
public class MainActivity extends AppCompatActivity {

    private SharedPreferences prefs;
    private WebView web;
    private LinearLayout pairScreen;
    private TextView status;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        prefs = getSharedPreferences("onehand", MODE_PRIVATE);
        setContentView(R.layout.activity_main);

        web = findViewById(R.id.web);
        pairScreen = findViewById(R.id.pair_screen);
        status = findViewById(R.id.status);
        EditText addr = findViewById(R.id.addr);
        Button connect = findViewById(R.id.connect);
        Button forget = findViewById(R.id.forget);

        ActivityCompat.requestPermissions(this,
                new String[]{Manifest.permission.RECORD_AUDIO}, 1);

        setupWebView();

        String saved = prefs.getString("url", null);
        if (saved != null) {
            addr.setText(saved);
            open(saved);
        }

        connect.setOnClickListener(v -> {
            String url = normalize(addr.getText().toString().trim());
            if (url == null) {
                status.setText("enter the address shown on your Mac, e.g. 192.168.1.214:8741/?pin=1234");
                return;
            }
            prefs.edit().putString("url", url).apply();
            open(url);
        });

        forget.setOnClickListener(v -> {
            prefs.edit().remove("url").apply();
            addr.setText("");
            status.setText("");
        });
    }

    /** Accepts "192.168.1.5:8741/?pin=1234" or a full https URL. */
    private String normalize(String s) {
        if (s.isEmpty()) return null;
        if (!s.startsWith("http")) s = "https://" + s;
        if (!s.contains("pin=")) return s;  // pin recommended but not forced here
        return s;
    }

    @SuppressLint("SetJavaScriptEnabled")
    private void setupWebView() {
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setMediaPlaybackRequiresUserGesture(false);

        web.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onPermissionRequest(PermissionRequest request) {
                // the page asks for the mic for dictation; grant it
                runOnUiThread(() -> request.grant(request.getResources()));
            }
        });

        web.setWebViewClient(new WebViewClient() {
            @Override
            @SuppressLint("WebViewClientOnReceivedSslError")
            public void onReceivedSslError(WebView view, SslErrorHandler handler, SslError error) {
                // onehand uses a self-signed cert on the LAN; trust it.
                // Only do this for private addresses to limit the blast radius.
                String host = android.net.Uri.parse(view.getUrl() == null ? "" : view.getUrl()).getHost();
                if (host != null && (host.startsWith("192.168.") || host.startsWith("10.")
                        || host.startsWith("172.") || host.equals("localhost"))) {
                    handler.proceed();
                } else {
                    handler.cancel();
                }
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest req, WebResourceError err) {
                if (req.isForMainFrame()) {
                    runOnUiThread(() -> {
                        showPairing();
                        status.setText("could not reach the Mac. is the onehand server running and are you on the same wifi?");
                    });
                }
            }
        });
    }

    private void open(String url) {
        pairScreen.setVisibility(View.GONE);
        web.setVisibility(View.VISIBLE);
        web.loadUrl(url);
    }

    private void showPairing() {
        web.setVisibility(View.GONE);
        pairScreen.setVisibility(View.VISIBLE);
    }

    @Override
    public void onBackPressed() {
        // back button returns to pairing screen instead of leaving the app
        if (web.getVisibility() == View.VISIBLE) showPairing();
        else super.onBackPressed();
    }
}
