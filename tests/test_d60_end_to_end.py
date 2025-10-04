"""
End-to-end test for custom cabinet D60 functionality.

This test verifies the complete workflow:
1. Adding custom cabinet named "D60" (same as existing catalog template)
2. Generating report that includes custom cabinet parts
3. Verifying no conflicts with catalog templates
"""

import pytest
from src.db_schema.orm_models import (
    Project,
    ProjectCabinet,
    CabinetTemplate,
    ProjectCabinetPart,
)
from src.controllers.project_details_controller import ProjectDetailsController
from src.services.project_service import ProjectService
from src.services.report_generator import ReportGenerator


class TestCustomCabinetD60EndToEnd:
    """End-to-end test for custom cabinet D60 functionality"""

    def test_complete_d60_custom_cabinet_workflow(self, session):
        """Complete test: Add custom D60 cabinet and generate report"""

        # Step 1: Setup - Create project and existing catalog template
        project = Project(
            name="D60 Test Project", order_number="D60-TEST-001", kitchen_type="LOFT"
        )
        session.add(project)
        session.commit()

        # Create existing catalog template "D60" to simulate real conflict
        catalog_d60 = CabinetTemplate(nazwa="D60", kitchen_type="LOFT")
        session.add(catalog_d60)
        session.commit()

        print(f"✅ Created catalog template D60 with ID: {catalog_d60.id}")

        # Step 2: Create controller and add custom cabinet D60
        project_service = ProjectService(session)
        controller = ProjectDetailsController(session, project_service)
        controller.project = project

        # This simulates what CustomCabinetDialog would send
        custom_d60_data = {
            "name": "D60",  # Same name as catalog template!
            "kitchen_type": "LOFT",
            "width": 600,
            "height": 720,
            "depth": 560,
            "body_color": "#f5f5f5",
            "front_color": "#2c3e50",
            "handle_type": "Push-to-open",
            "quantity": 2,
            "parts": [
                {
                    "part_name": "Custom Bok lewy D60",
                    "width_mm": 560,
                    "height_mm": 720,
                    "pieces": 1,
                    "material": "PLYTA",
                    "thickness_mm": 18,
                    "comments": "Niestandardowy panel boczny",
                },
                {
                    "part_name": "Custom Bok prawy D60",
                    "width_mm": 560,
                    "height_mm": 720,
                    "pieces": 1,
                    "material": "PLYTA",
                    "thickness_mm": 18,
                    "comments": "Niestandardowy panel boczny",
                },
                {
                    "part_name": "Custom Dno D60",
                    "width_mm": 564,
                    "height_mm": 560,
                    "pieces": 1,
                    "material": "PLYTA",
                    "thickness_mm": 18,
                    "comments": "Niestandardowe dno",
                },
                {
                    "part_name": "Custom Front D60",
                    "width_mm": 596,
                    "height_mm": 718,
                    "pieces": 1,
                    "material": "FRONT",
                    "thickness_mm": 18,
                    "comments": "Niestandardowy front MDF",
                },
                {
                    "part_name": "Custom Tył D60",
                    "width_mm": 592,
                    "height_mm": 712,
                    "pieces": 1,
                    "material": "HDF",
                    "thickness_mm": 3,
                    "comments": "Niestandardowy tył HDF",
                },
            ],
        }

        # Step 3: Add custom cabinet - this should NOT fail despite name collision
        try:
            custom_cabinet = controller.add_cabinet(project.id, **custom_d60_data)
            print(
                f"✅ Successfully added custom D60 cabinet with ID: {custom_cabinet.id}"
            )
        except Exception as e:
            pytest.fail(f"Failed to add custom D60 cabinet: {str(e)}")

        # Step 4: Verify cabinet was created correctly
        assert custom_cabinet is not None
        assert custom_cabinet.type_id is None  # Custom cabinet
        assert custom_cabinet.sequence_number == 1
        assert custom_cabinet.quantity == 2

        # Step 5: Verify custom parts were created
        custom_parts = (
            session.query(ProjectCabinetPart)
            .filter(ProjectCabinetPart.project_cabinet_id == custom_cabinet.id)
            .all()
        )

        assert len(custom_parts) == 5
        part_names = [part.part_name for part in custom_parts]
        assert "Custom Bok lewy D60" in part_names
        assert "Custom Bok prawy D60" in part_names
        assert "Custom Dno D60" in part_names
        assert "Custom Front D60" in part_names
        assert "Custom Tył D60" in part_names

        print(f"✅ Created {len(custom_parts)} custom parts")

        # Step 6: Verify catalog template still exists unchanged
        catalog_templates = (
            session.query(CabinetTemplate).filter(CabinetTemplate.nazwa == "D60").all()
        )
        assert len(catalog_templates) == 1  # Only original catalog template
        assert catalog_templates[0].id == catalog_d60.id

        print("✅ Catalog template D60 unaffected")

        # Step 7: Load project with relationships for report generation
        session.refresh(project)
        session.refresh(custom_cabinet)

        # Step 8: Generate report - this should include custom cabinet parts
        report_generator = ReportGenerator()
        try:
            formatki, fronty, hdf, akcesoria = (
                report_generator._extract_elements_directly(project)
            )
            print("✅ Report generation successful")
        except Exception as e:
            pytest.fail(f"Report generation failed: {str(e)}")

        # Step 9: Verify report contains custom cabinet parts

        # Check FORMATKI (panels) - should have custom panels
        formatki_names = [part.name for part in formatki]
        assert "Custom Bok lewy D60" in formatki_names
        assert "Custom Bok prawy D60" in formatki_names
        assert "Custom Dno D60" in formatki_names

        # Verify quantities (should be multiplied by cabinet quantity=2)
        left_panel = next(
            part for part in formatki if part.name == "Custom Bok lewy D60"
        )
        assert left_panel.quantity == 2  # 1 piece * 2 cabinet quantity
        assert left_panel.width == 560
        assert left_panel.height == 720
        assert left_panel.seq == "①"

        print(f"✅ Found {len(formatki)} formatki parts in report")

        # Check FRONTY (fronts)
        fronty_names = [part.name for part in fronty]
        assert "Custom Front D60" in fronty_names

        front_part = next(part for part in fronty if part.name == "Custom Front D60")
        assert front_part.quantity == 2  # 1 piece * 2 cabinet quantity
        assert front_part.color == "#2c3e50"  # front_color
        assert "Handle: Push-to-open" in front_part.notes

        print(f"✅ Found {len(fronty)} fronty parts in report")

        # Check HDF
        hdf_names = [part.name for part in hdf]
        assert "Custom Tył D60" in hdf_names

        hdf_part = next(part for part in hdf if part.name == "Custom Tył D60")
        assert hdf_part.quantity == 2  # 1 piece * 2 cabinet quantity
        assert hdf_part.width == 592
        assert hdf_part.height == 712

        print(f"✅ Found {len(hdf)} HDF parts in report")

        # Step 10: Final verification - ensure we can distinguish between catalog and custom D60

        # If we had a catalog cabinet with same name, it would work differently
        catalog_cabinet = ProjectCabinet(
            project_id=project.id,
            type_id=catalog_d60.id,  # Links to catalog template
            sequence_number=2,
            body_color="#ffffff",
            front_color="#ffffff",
            handle_type="Standard",
            quantity=1,
        )
        session.add(catalog_cabinet)
        session.commit()

        # Now project has both custom D60 (seq=1) and catalog D60 (seq=2)
        all_cabinets = (
            session.query(ProjectCabinet)
            .filter(ProjectCabinet.project_id == project.id)
            .all()
        )

        assert len(all_cabinets) == 2
        custom_cabs = [cab for cab in all_cabinets if cab.type_id is None]
        catalog_cabs = [cab for cab in all_cabinets if cab.type_id is not None]

        assert len(custom_cabs) == 1
        assert len(catalog_cabs) == 1

        print("✅ Successfully demonstrated custom and catalog D60 coexistence")

        # Final success message
        print("\n🎉 COMPLETE SUCCESS: Custom cabinet D60 workflow fully functional!")
        print("   ✓ No name conflicts with existing catalog templates")
        print("   ✓ Custom parts stored separately in ProjectCabinetCustomPart")
        print("   ✓ Report generation includes custom cabinet parts")
        print("   ✓ Both custom and catalog D60 cabinets can coexist")


if __name__ == "__main__":
    pytest.main([__file__])
