package org.telegram.spectra;

import androidx.exifinterface.media.ExifInterface;

import java.io.File;

/**
 * Strips privacy-sensitive EXIF metadata from images before sending.
 * Keeps only orientation and pixel dimensions.
 */
public final class SpectraExifCleaner {

    private SpectraExifCleaner() {}

    private static final String[] PRIVACY_TAGS = {
            "GPSVersionID", "GPSLatitude", "GPSLatitudeRef", "GPSLongitude", "GPSLongitudeRef",
            "GPSAltitude", "GPSAltitudeRef", "GPSTimestamp", "GPSProcessingMethod", "GPSDateStamp",
            "GPSSpeed", "GPSSpeedRef", "GPSDestBearing", "GPSDestBearingRef",
            "Make", "Model", "Software", "Artist", "Copyright", "OwnerName",
            "SerialNumber", "LensMake", "LensModel", "LensSerialNumber",
            "DateTimeOriginal", "DateTimeDigitized", "SubSecTime", "SubSecTimeOriginal", "SubSecTimeDigitized",
            "ImageUniqueID", "CameraOwnerName", "BodySerialNumber"
    };

    /** Cleans the file in place; returns true if EXIF was rewritten. */
    public static boolean clean(File file) {
        if (file == null || !file.exists()) return false;
        if (!SpectraConfig.isStripExif()) return false;
        try {
            ExifInterface exif = new ExifInterface(file.getAbsolutePath());
            for (String tag : PRIVACY_TAGS) {
                exif.setAttribute(tag, null);
            }
            exif.saveAttributes();
            return true;
        } catch (Throwable t) {
            return false;
        }
    }
}
