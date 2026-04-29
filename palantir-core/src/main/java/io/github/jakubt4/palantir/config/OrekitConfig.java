package io.github.jakubt4.palantir.config;

import jakarta.annotation.PostConstruct;
import lombok.extern.slf4j.Slf4j;
import org.orekit.data.DataContext;
import org.orekit.data.ZipJarCrawler;
import org.springframework.context.annotation.Configuration;

/**
 * Bootstraps the Orekit astrodynamics library by registering {@code orekit-data.zip}
 * (Earth orientation parameters, leap seconds, etc.) with Orekit's {@link DataContext}.
 *
 * <p>Must initialize before any Orekit API call. Other beans that depend on Orekit
 * should inject this configuration to guarantee ordering.
 */
@Slf4j
@Configuration
public class OrekitConfig {

    /**
     * Loads {@code orekit-data.zip} from the classpath into Orekit's
     * {@link org.orekit.data.DataProvidersManager}.
     *
     * @throws IllegalStateException if the archive is not found on the classpath
     */
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
