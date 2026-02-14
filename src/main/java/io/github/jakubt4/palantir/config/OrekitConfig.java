package io.github.jakubt4.palantir.config;

import jakarta.annotation.PostConstruct;
import lombok.extern.slf4j.Slf4j;
import org.orekit.data.DataContext;
import org.orekit.data.ZipJarCrawler;
import org.springframework.context.annotation.Configuration;

@Slf4j
@Configuration
public class OrekitConfig {

    @PostConstruct
    public void init() {
        final var orekitData = OrekitConfig.class.getClassLoader().getResource("orekit-data.zip");
        if (orekitData == null) {
            throw new IllegalStateException("orekit-data.zip not found on classpath");
        }
        final var crawler = new ZipJarCrawler(orekitData);
        DataContext.getDefault().getDataProvidersManager().addProvider(crawler);
        log.info("Orekit data loaded from classpath:orekit-data.zip");
    }
}
