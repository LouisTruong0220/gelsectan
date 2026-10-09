plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "vn.roboworld.chibach"
    compileSdk = 34

    defaultConfig {
        applicationId = "vn.roboworld.chibach"
        minSdk = 26          // Android 8.0 â€” má»©c tá»‘i thiá»ƒu Agent SDK yÃªu cáº§u
        targetSdk = 34
        versionCode = 4
        versionName = "1.3"
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
    kotlinOptions { jvmTarget = "11" }

    buildTypes {
        release { isMinifyEnabled = false }
    }

    // index.html Ä‘Ã£ nÃ©n sáºµn 1,5 MB; Ä‘á»ƒ nguyÃªn cho WebView Ä‘á»c tháº³ng tá»« assets
    androidResources { noCompress += listOf("html") }
}

dependencies {
    /*
     * Agent SDK â€” táº§ng há»™i thoáº¡i AI cá»§a OrionStar. Láº¥y tá»« GÃ“I OFFLINE cá»§a hÃ£ng,
     * náº±m á»Ÿ libs/ (sdk-0.4.7.aar + agent-base-0.2.10.aar).
     *
     * âš  TUYá»†T Äá»I KHÃ”NG quay láº¡i JitPack `com.github.orionagent:agent-sdk`.
     *   Cáº£ bá»‘n báº£n trÃªn Ä‘Ã³ (0.2.2 Â· 0.2.3 Â· 0.2.4 Â· 0.2.5) Ä‘á»u GHI Cá»¨NG sai tÃªn gÃ³i
     *   dá»‹ch vá»¥ â€” `com.ainirobot.speechasrservice` trong khi ROM mÃ¡y nÃ y Ä‘á»ƒ dá»‹ch vá»¥ á»Ÿ
     *   `com.ainirobot.agentservice`. SDK khÃ´ng bind Ä‘Æ°á»£c, nÃªn má»i lá»‡nh `AgentCore.*`
     *   láº·ng láº½ khÃ´ng lÃ m gÃ¬: khÃ´ng lá»—i, khÃ´ng callback, khÃ´ng log. App tra cá»©u thá»§ tá»¥c
     *   cÃ¢m micro suá»‘t hai tuáº§n vÃ¬ Ä‘Ãºng chuyá»‡n nÃ y.
     *   HÃ£ng xÃ¡c nháº­n 11/08/2026: JitPack lÃ  kÃªnh cÅ© thá»i 0.2.x, Ä‘Ã£ ngá»«ng báº£o trÃ¬.
     *   Cáº§n báº£n má»›i hÆ¡n 0.4.7 thÃ¬ xin hÃ£ng gÃ³i offline má»›i, Ä‘á»«ng tá»± tÃ¬m trÃªn máº¡ng.
     *
     * Robot SDK â€” táº§ng Ä‘iá»u khiá»ƒn pháº§n cá»©ng (dáº«n Ä‘Æ°á»ng, giá»ng nÃ³i): robotservice.jar.
     * âš  robotservice.jar cáº§n Gson nhÆ°ng KHÃ”NG Ä‘Ã³ng gÃ³i kÃ¨m â€” thiáº¿u dÃ²ng gson bÃªn dÆ°á»›i
     *   thÃ¬ RobotApi.connectServer nÃ©m ClassNotFoundException, app vÄƒng ngay lÃºc káº¿t ná»‘i.
     */
    implementation(fileTree(mapOf("dir" to "libs", "include" to listOf("*.jar", "*.aar"))))
    implementation("com.google.code.gson:gson:2.10.1")

    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.appcompat:appcompat:1.6.1")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3")
}
